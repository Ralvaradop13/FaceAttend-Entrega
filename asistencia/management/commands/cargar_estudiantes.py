
import csv

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from asistencia.models import Estudiante


class Command(BaseCommand):
    help = "Carga estudiantes desde estudiantes.csv"

    def handle(self, *args, **options):

        archivo = settings.BASE_DIR / "estudiantes.csv"

        if not archivo.exists():
            raise CommandError(
                "No se encuentra estudiantes.csv"
            )

        total = 0

        with open(
            archivo,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as f:

            lector = csv.DictReader(f)

            for fila in lector:

                codigo = fila["codigo"].strip()
                nombre = fila["nombre"].strip()

                if not codigo or not nombre:
                    continue

                Estudiante.objects.update_or_create(
                    codigo=codigo,
                    defaults={
                        "nombre": nombre,
                        "activo": True
                    }
                )

                total += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Estudiantes procesados: {total}"
            )
        )
