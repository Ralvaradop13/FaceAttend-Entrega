"""Práctica 4 - Pruebas unitarias, de integración y funcionales de FaceAttend.

Ejecutar desde la carpeta que contiene manage.py:
    python manage.py test asistencia -v 2

No utiliza fotos reales, webcam ni el modelo entrenado de los participantes.
"""

import base64
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import cv2
import numpy as np
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from asistencia.management.commands.entrenar_rostros import (
    ajustar_imagen,
    detectar_rostro,
    seleccionar_rostro,
)
from asistencia.models import Asistencia, Estudiante, SesionAsistencia
from asistencia.reconocedor import reconocer_rostro


class DetectorSimulado:
    """Simula la detección Haar sin acceder a webcam ni fotos personales."""

    def __init__(self, rostros):
        self.rostros = np.array(rostros, dtype=np.int32).reshape((-1, 4))

    def empty(self):
        return False

    def detectMultiScale(self, _imagen, **_opciones):
        return self.rostros


class PruebasUnitariasImagen(TestCase):
    """Pruebas unitarias de funciones que utilizan OpenCV."""

    def test_redimensionar_imagen_grande(self):
        imagen = np.zeros((2400, 1800, 3), dtype=np.uint8)
        resultado = ajustar_imagen(imagen)
        self.assertEqual(max(resultado.shape[:2]), 1600)

    def test_imagen_pequena_no_se_redimensiona(self):
        imagen = np.zeros((240, 320, 3), dtype=np.uint8)
        resultado = ajustar_imagen(imagen)
        self.assertEqual(resultado.shape, imagen.shape)

    def test_seleccionar_rostro_principal(self):
        detecciones = [(10, 10, 40, 40), (50, 50, 160, 160)]
        principal = seleccionar_rostro(detecciones, 400, 400)
        self.assertEqual(principal, (50, 50, 160, 160))

    def test_rechazar_rostros_ambiguos(self):
        detecciones = [(20, 20, 120, 120), (180, 20, 110, 110)]
        principal = seleccionar_rostro(detecciones, 400, 300)
        self.assertIsNone(principal)

    def test_detectar_y_preprocesar_rostro_simulado(self):
        imagen = np.full((300, 300, 3), 128, dtype=np.uint8)
        resultado = detectar_rostro(
            imagen,
            [DetectorSimulado([(50, 50, 140, 140)])],
        )
        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.shape, (160, 160))
        self.assertEqual(resultado.dtype, np.uint8)


class PruebasUnitariasReconocedor(TestCase):
    """Pruebas del umbral LBPH y del enlace con SQLite."""

    @classmethod
    def setUpTestData(cls):
        cls.estudiante = Estudiante.objects.create(
            codigo="PRU001", nombre="Estudiante de prueba", activo=True
        )

    def _predecir_con_modelo_simulado(self, etiqueta, distancia):
        with TemporaryDirectory() as temporal:
            carpeta = Path(temporal) / "modelos"
            carpeta.mkdir()
            (carpeta / "rostros_lbph.yml").write_text("modelo simulado")
            modelo = Mock()
            modelo.predict.return_value = (etiqueta, distancia)
            with override_settings(BASE_DIR=Path(temporal)):
                with patch(
                    "asistencia.reconocedor.cargar_modelo", return_value=modelo
                ):
                    resultado = reconocer_rostro(
                        np.full((160, 160), 125, dtype=np.uint8)
                    )
            return resultado

    def test_aceptar_coincidencia_bajo_umbral(self):
        resultado = self._predecir_con_modelo_simulado(
            self.estudiante.id, 45.0
        )
        self.assertTrue(resultado["identificado"])
        self.assertEqual(resultado["estudiante_id"], self.estudiante.id)

    def test_rechazar_coincidencia_sobre_umbral(self):
        resultado = self._predecir_con_modelo_simulado(
            self.estudiante.id, 90.0
        )
        self.assertFalse(resultado["identificado"])
        self.assertEqual(resultado["nombre"], "Desconocido")

    def test_rechazar_identificador_no_registrado(self):
        resultado = self._predecir_con_modelo_simulado(999999, 35.0)
        self.assertFalse(resultado["identificado"])

    def test_error_si_no_existe_modelo(self):
        with TemporaryDirectory() as temporal:
            with override_settings(BASE_DIR=Path(temporal)):
                with self.assertRaises(FileNotFoundError):
                    reconocer_rostro(np.zeros((160, 160), dtype=np.uint8))


class PruebasIntegracionYFuncionales(TestCase):
    """Pruebas HTTP de Django con fotogramas JPEG generados artificialmente."""

    @classmethod
    def setUpTestData(cls):
        cls.estudiante = Estudiante.objects.create(
            codigo="PRU002", nombre="Persona de demostración", activo=True
        )

    @staticmethod
    def _fotograma_json():
        imagen = np.full((240, 320, 3), 140, dtype=np.uint8)
        codificado, jpeg = cv2.imencode(".jpg", imagen)
        assert codificado, "OpenCV no pudo generar el JPEG de prueba"
        cadena = base64.b64encode(jpeg.tobytes()).decode("ascii")
        return json.dumps({"imagen": "data:image/jpeg;base64," + cadena})

    def _enviar_fotograma(self):
        return self.client.post(
            reverse("detectar_rostros"),
            data=self._fotograma_json(),
            content_type="application/json",
        )

    def test_pagina_principal_responde_y_muestra_contadores(self):
        respuesta = self.client.get(reverse("inicio"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "FaceAttend")
        self.assertContains(respuesta, "Estudiantes registrados")
        self.assertContains(respuesta, "Asistencias del día")

    def test_endpoint_rechaza_metodo_get(self):
        respuesta = self.client.get(reverse("detectar_rostros"))
        self.assertEqual(respuesta.status_code, 405)

    def test_endpoint_rechaza_formato_incorrecto(self):
        respuesta = self.client.post(
            reverse("detectar_rostros"),
            data=json.dumps({"imagen": "sin-imagen"}),
            content_type="application/json",
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_endpoint_rechaza_base64_danado(self):
        respuesta = self.client.post(
            reverse("detectar_rostros"),
            data=json.dumps({"imagen": "data:image/jpeg;base64,!!invalido!!"}),
            content_type="application/json",
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_fotograma_sin_rostros_no_registra_asistencia(self):
        with patch(
            "asistencia.views.detector", DetectorSimulado([])
        ):
            respuesta = self._enviar_fotograma()
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(datos["rostros"], [])
        self.assertEqual(datos["asistencia"]["estado"], "SIN_IDENTIFICAR")
        self.assertEqual(Asistencia.objects.count(), 0)

    def test_identidad_desconocida_no_registra_asistencia(self):
        desconocido = {
            "estudiante_id": None,
            "nombre": "Desconocido",
            "identificado": False,
            "distancia": 94.5,
        }
        with patch(
            "asistencia.views.detector",
            DetectorSimulado([(65, 45, 100, 100)]),
        ), patch("asistencia.views.reconocer_rostro", return_value=desconocido):
            respuesta = self._enviar_fotograma()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["asistencia"]["estado"], "SIN_IDENTIFICAR")
        self.assertEqual(Asistencia.objects.count(), 0)

    def test_cuatro_coincidencias_registran_una_sola_asistencia(self):
        reconocido = {
            "estudiante_id": self.estudiante.id,
            "nombre": self.estudiante.nombre,
            "identificado": True,
            "distancia": 41.0,
        }
        with patch(
            "asistencia.views.detector",
            DetectorSimulado([(65, 45, 100, 100)]),
        ), patch("asistencia.views.reconocer_rostro", return_value=reconocido):
            estados = [
                self._enviar_fotograma().json()["asistencia"]["estado"]
                for _ in range(5)
            ]
        self.assertEqual(estados[:3], ["VERIFICANDO"] * 3)
        self.assertEqual(estados[3], "REGISTRADA")
        self.assertEqual(estados[4], "YA_REGISTRADA")
        self.assertEqual(Asistencia.objects.count(), 1)
        self.assertEqual(SesionAsistencia.objects.count(), 1)
        pagina = self.client.get(reverse("inicio"))
        self.assertEqual(pagina.context["resumen"]["presentes"], 1)
        self.assertEqual(pagina.context["resumen"]["pendientes"], 0)

    def test_sesion_cerrada_no_permita_registro(self):
        SesionAsistencia.objects.create(
            fecha=timezone.localdate(), estado="CERRADA"
        )
        reconocido = {
            "estudiante_id": self.estudiante.id,
            "nombre": self.estudiante.nombre,
            "identificado": True,
            "distancia": 42.0,
        }
        with patch(
            "asistencia.views.detector",
            DetectorSimulado([(65, 45, 100, 100)]),
        ), patch("asistencia.views.reconocer_rostro", return_value=reconocido):
            respuestas = [self._enviar_fotograma() for _ in range(4)]
        self.assertEqual(
            respuestas[-1].json()["asistencia"]["estado"], "CERRADA"
        )
        self.assertEqual(Asistencia.objects.count(), 0)

    def test_base_de_datos_impide_asistencia_duplicada(self):
        sesion = SesionAsistencia.objects.create(fecha=timezone.localdate())
        Asistencia.objects.create(estudiante=self.estudiante, sesion=sesion)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Asistencia.objects.create(
                    estudiante=self.estudiante, sesion=sesion
                )
        self.assertEqual(Asistencia.objects.count(), 1)
