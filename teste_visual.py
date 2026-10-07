"""Testes do padrao visual. Precisa de matplotlib (ao contrario dos testes do
coletor, que rodam so com a biblioteca padrao).

Uso: python teste_visual.py
"""
import os
import shutil
import tempfile
import unittest

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import visual


def textos(fig):
    return [t.get_text() for t in fig.texts]


class TesteGrafico(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_titulo_subtitulo_e_fonte(self):
        fig, _ = visual.grafico("Titulo", subtitulo="Sub")
        self.assertEqual(textos(fig), ["Titulo", "Sub", visual.FONTE_FRAUDE])

    def test_sem_subtitulo_nem_fonte(self):
        fig, _ = visual.grafico("Titulo", fonte=None)
        self.assertEqual(textos(fig), ["Titulo"])

    def test_titulo_alinhado_a_esquerda(self):
        fig, _ = visual.grafico("Titulo")
        self.assertEqual(fig.texts[0].get_ha(), "left")

    def test_sem_borda_de_cima_e_da_direita(self):
        _, ax = visual.grafico("Titulo")
        self.assertFalse(ax.spines["top"].get_visible())
        self.assertFalse(ax.spines["right"].get_visible())
        self.assertTrue(ax.spines["left"].get_visible())

    def test_grade_so_horizontal(self):
        _, ax = visual.grafico("Titulo")
        self.assertTrue(any(l.get_visible() for l in ax.yaxis.get_gridlines()))
        self.assertFalse(any(l.get_visible() for l in ax.xaxis.get_gridlines()))

    def test_cores_seguem_a_ordem_fixa(self):
        _, ax = visual.grafico("Titulo")
        linhas = [ax.plot([0, 1], [0, 1])[0] for _ in range(3)]
        self.assertEqual([l.get_color() for l in linhas], visual.CATEGORICAS[:3])

    def test_varias_linhas_compartilham_o_eixo_x(self):
        _, eixos = visual.grafico("Titulo", linhas=2)
        self.assertEqual(len(eixos), 2)
        self.assertTrue(eixos[0].get_shared_x_axes().joined(eixos[0], eixos[1]))

    def test_titulo_longo_reserva_mais_espaco(self):
        fig1, _ = visual.grafico("Uma linha")
        fig2, _ = visual.grafico("Duas\nlinhas")
        self.assertGreater(fig2._espaco_reservado[0], fig1._espaco_reservado[0])


class TesteSalvar(unittest.TestCase):
    def setUp(self):
        self.original = os.getcwd()
        self.raiz = tempfile.mkdtemp()

    def tearDown(self):
        os.chdir(self.original)
        shutil.rmtree(self.raiz)
        plt.close("all")

    def test_dentro_do_repositorio_grava_em_graficos_ao_lado(self):
        os.makedirs(os.path.join(self.raiz, "graficos"))
        os.makedirs(os.path.join(self.raiz, "notebooks"))
        os.chdir(os.path.join(self.raiz, "notebooks"))
        fig, _ = visual.grafico("Titulo")
        caminho = visual.salvar(fig, "teste.png")
        self.assertTrue(os.path.exists(os.path.join(self.raiz, "graficos", "teste.png")))
        self.assertEqual(caminho, os.path.join("../graficos", "teste.png"))

    def test_fora_do_repositorio_cria_graficos_na_pasta_atual(self):
        # no Colab a pasta de trabalho e /content e ../graficos nao existe
        os.chdir(self.raiz)
        fig, _ = visual.grafico("Titulo")
        visual.salvar(fig, "teste.png")
        self.assertTrue(os.path.exists(os.path.join(self.raiz, "graficos", "teste.png")))


if __name__ == "__main__":
    unittest.main()
