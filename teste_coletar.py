"""Testes do coletor.

Uso: python teste_coletar.py
"""
import io
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError

import coletar


class TesteRequisitar(unittest.TestCase):
    @patch("coletar.urllib.request.urlopen")
    def test_200(self, urlopen_mock):
        resposta = MagicMock()
        resposta.status = 200
        resposta.read.return_value = b'{"ok": true}'
        resposta.__enter__.return_value = resposta
        urlopen_mock.return_value = resposta

        status, corpo = coletar.requisitar("http://exemplo")
        self.assertEqual(status, 200)
        self.assertEqual(corpo, '{"ok": true}')

    @patch("coletar.urllib.request.urlopen")
    def test_400(self, urlopen_mock):
        urlopen_mock.side_effect = HTTPError(
            "http://exemplo", 400, "Bad Request", {}, io.BytesIO(b"parametro invalido")
        )
        status, corpo = coletar.requisitar("http://exemplo")
        self.assertEqual(status, 400)

    @patch("coletar.urllib.request.urlopen")
    def test_500(self, urlopen_mock):
        urlopen_mock.side_effect = HTTPError(
            "http://exemplo", 500, "Server Error", {}, io.BytesIO(b"erro interno")
        )
        status, _ = coletar.requisitar("http://exemplo")
        self.assertEqual(status, 500)

    @patch("coletar.urllib.request.urlopen")
    def test_falha_de_rede_nao_levanta_excecao(self, urlopen_mock):
        urlopen_mock.side_effect = URLError("timed out")
        status, corpo = coletar.requisitar("http://exemplo")
        self.assertIsNone(status)
        self.assertIsNone(corpo)


class TesteDesembrulhar(unittest.TestCase):
    def test_json_embrulhado(self):
        corpo = '/**/{"value": [1, 2]}'
        self.assertEqual(coletar.desembrulhar(corpo), {"value": [1, 2]})

    def test_json_puro(self):
        corpo = '{"value": [1, 2]}'
        self.assertEqual(coletar.desembrulhar(corpo), {"value": [1, 2]})

    def test_html_devolve_none(self):
        corpo = "<html><body>erro</body></html>"
        self.assertIsNone(coletar.desembrulhar(corpo))

    def test_corpo_vazio_devolve_none(self):
        self.assertIsNone(coletar.desembrulhar(""))
        self.assertIsNone(coletar.desembrulhar(None))


class TesteMontarUrl(unittest.TestCase):
    def test_database_com_d_minusculo(self):
        url = coletar.montar_url("EstatisticasFraudesPix", "Database", 202201)
        self.assertIn("Database=@Database", url)
        self.assertIn("@Database='202201'", url)

    def test_database_com_b_maiusculo(self):
        url = coletar.montar_url("TransacoesPixPorMunicipio", "DataBase", 202201)
        self.assertIn("DataBase=@DataBase", url)
        self.assertIn("@DataBase='202201'", url)


class TesteGerarMeses(unittest.TestCase):
    def test_virada_de_ano(self):
        self.assertEqual(
            coletar.gerar_meses(202411, 202502),
            [202411, 202412, 202501, 202502],
        )

    def test_mesmo_mes(self):
        self.assertEqual(coletar.gerar_meses(202401, 202401), [202401])


class TesteColetarMes(unittest.TestCase):
    @patch("coletar.requisitar")
    def test_sucesso(self, requisitar_mock):
        requisitar_mock.return_value = (200, '{"value": [{"AnoMes": 202201}]}')
        linhas, situacao = coletar.coletar_mes("fraude", 202201)
        self.assertEqual(linhas, [{"AnoMes": 202201}])
        self.assertEqual(situacao, "ok")

    @patch("coletar.requisitar")
    def test_mes_vazio(self, requisitar_mock):
        requisitar_mock.return_value = (200, '{"value": []}')
        linhas, situacao = coletar.coletar_mes("fraude", 202201)
        self.assertEqual(linhas, [])
        self.assertEqual(situacao, "vazio")

    @patch("coletar.requisitar")
    def test_erro_400_nao_reentrega(self, requisitar_mock):
        requisitar_mock.return_value = (400, "parametro invalido")
        coletar.coletar_mes("fraude", 202201)
        self.assertEqual(requisitar_mock.call_count, 1)

    @patch("coletar.time.sleep", return_value=None)
    @patch("coletar.requisitar")
    def test_erro_500_reentrega_e_desiste(self, requisitar_mock, sleep_mock):
        requisitar_mock.return_value = (500, "erro interno")
        _, situacao = coletar.coletar_mes("fraude", 202201)
        self.assertEqual(requisitar_mock.call_count, coletar.TENTATIVAS)
        self.assertEqual(situacao, "falha_rede")

    @patch("coletar.time.sleep", return_value=None)
    @patch("coletar.requisitar")
    def test_500_depois_sucesso(self, requisitar_mock, sleep_mock):
        requisitar_mock.side_effect = [
            (500, "erro interno"),
            (200, '{"value": [{"AnoMes": 202201}]}'),
        ]
        linhas, situacao = coletar.coletar_mes("fraude", 202201)
        self.assertEqual(situacao, "ok")
        self.assertEqual(len(linhas), 1)


if __name__ == "__main__":
    unittest.main()
