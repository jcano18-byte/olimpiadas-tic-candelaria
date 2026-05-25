"""
Anade 5 preguntas a cada JSON de examen para llegar a 25.
Las preguntas nuevas mantienen tipos mezclados y respetan los temas
ya definidos por grado.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EXAMS = BASE / "exams"

NEW = {
    "grade6": [
        {
            "id": 21,
            "type": "argumentativa",
            "topic": "Software y hardware",
            "difficulty": "media",
            "text": "¿Por qué es importante hacer copias de seguridad (backup) de los archivos?",
            "choices": {
                "A": "Para que el computador encienda más rápido.",
                "B": "Para no perder información si el dispositivo falla o se daña.",
                "C": "Para reducir el tamaño del disco duro.",
                "D": "Porque lo exige el navegador."
            },
            "answer": "B"
        },
        {
            "id": 22,
            "type": "propositiva",
            "topic": "Artefactos tecnológicos",
            "difficulty": "media",
            "text": "Si quieres reducir el desperdicio de agua en tu casa, ¿qué artefacto tecnológico ayudaría más?",
            "choices": {
                "A": "Una regadera con limitador de caudal.",
                "B": "Una televisión nueva.",
                "C": "Un teclado inalámbrico.",
                "D": "Una impresora a color."
            },
            "answer": "A"
        },
        {
            "id": 23,
            "type": "interpretativa",
            "topic": "Sistema operativo",
            "difficulty": "media",
            "text": "El 'escritorio' en un sistema operativo es:",
            "choices": {
                "A": "El mueble donde está el computador.",
                "B": "La pantalla principal con accesos directos a programas y archivos.",
                "C": "Un programa para hacer dibujos.",
                "D": "Un tipo de impresora."
            },
            "answer": "B"
        },
        {
            "id": 24,
            "type": "argumentativa",
            "topic": "Navegadores",
            "difficulty": "media",
            "text": "¿Por qué es recomendable usar contraseñas distintas para diferentes cuentas?",
            "choices": {
                "A": "Para llenar más espacio en la memoria.",
                "B": "Para que si una contraseña se descubre, no se pierdan todas las cuentas.",
                "C": "Para que el navegador funcione más rápido.",
                "D": "Para complicar el inicio de sesión sin razón."
            },
            "answer": "B"
        },
        {
            "id": 25,
            "type": "interpretativa",
            "topic": "Navegadores",
            "difficulty": "media",
            "text": "Una URL es:",
            "choices": {
                "A": "El nombre de un virus informático.",
                "B": "La dirección única de una página web (ej. https://midominio.com).",
                "C": "Un tipo de archivo de imagen.",
                "D": "Un programa antivirus."
            },
            "answer": "B"
        }
    ],
    "grade7": [
        {
            "id": 21,
            "type": "argumentativa",
            "topic": "Materiales",
            "difficulty": "media",
            "text": "¿Por qué el vidrio se usa para envases de alimentos y medicinas?",
            "choices": {
                "A": "Porque es inerte (no reacciona) y permite ver el contenido.",
                "B": "Porque se rompe fácilmente y eso es bueno.",
                "C": "Porque cambia el sabor del producto.",
                "D": "Porque conserva mejor sin tapa."
            },
            "answer": "A"
        },
        {
            "id": 22,
            "type": "propositiva",
            "topic": "Materiales",
            "difficulty": "media",
            "text": "Para un proyecto escolar al aire libre que debe resistir lluvia y sol, ¿qué material es el más adecuado?",
            "choices": {
                "A": "Cartón sin recubrimiento.",
                "B": "Plástico resistente o lona impermeable.",
                "C": "Papel de seda.",
                "D": "Telas delicadas."
            },
            "answer": "B"
        },
        {
            "id": 23,
            "type": "interpretativa",
            "topic": "Ofimática",
            "difficulty": "media",
            "text": "En Google Drive / OneDrive, compartir un archivo con permiso de 'solo lectura' significa que la otra persona puede:",
            "choices": {
                "A": "Editar y borrar el archivo.",
                "B": "Ver el archivo pero no modificarlo.",
                "C": "Cambiar el nombre del propietario.",
                "D": "Convertirlo en imagen automáticamente."
            },
            "answer": "B"
        },
        {
            "id": 24,
            "type": "propositiva",
            "topic": "Ofimática",
            "difficulty": "media",
            "text": "Para crear el informe del proyecto con varios autores trabajando al mismo tiempo, lo más adecuado es:",
            "choices": {
                "A": "Cada uno escribe en su computador y luego copia y pega.",
                "B": "Usar un documento compartido en la nube (Docs / Word Online).",
                "C": "Enviarse el archivo por correo cada vez que cambia algo.",
                "D": "Imprimirlo y pasarlo de mano en mano."
            },
            "answer": "B"
        },
        {
            "id": 25,
            "type": "analisis_grafica",
            "topic": "Organizadores gráficos",
            "difficulty": "media",
            "text": "Observa: dos círculos que se cruzan. Izquierda solo: 'salado'. Intersección: 'comestible'. Derecha solo: 'dulce'. Este organizador es un:",
            "choices": {
                "A": "Diagrama de Venn.",
                "B": "Gráfico de barras.",
                "C": "Mapa conceptual.",
                "D": "Línea de tiempo."
            },
            "answer": "A",
            "image": "g7_q25_venn.png"
        }
    ],
    "grade8": [
        {
            "id": 21,
            "type": "argumentativa",
            "topic": "Máquinas simples",
            "difficulty": "media",
            "text": "¿Por qué la cuña (ej. el filo de un cuchillo) facilita cortar?",
            "choices": {
                "A": "Porque concentra la fuerza en un área pequeña y separa los materiales.",
                "B": "Porque calienta el material al rozarlo.",
                "C": "Porque pesa más que el material.",
                "D": "Porque distribuye la fuerza en un área grande."
            },
            "answer": "A"
        },
        {
            "id": 22,
            "type": "propositiva",
            "topic": "Máquinas compuestas",
            "difficulty": "media",
            "text": "Para diseñar una grúa escolar que levante una caja con poco esfuerzo, ¿qué combinación es la más adecuada?",
            "choices": {
                "A": "Polea + palanca + manivela.",
                "B": "Solo una cuña.",
                "C": "Una rueda suelta.",
                "D": "Un tornillo y nada más."
            },
            "answer": "A"
        },
        {
            "id": 23,
            "type": "interpretativa",
            "topic": "Máquinas de Goldberg",
            "difficulty": "media",
            "text": "Una característica esencial de una máquina de Goldberg es:",
            "choices": {
                "A": "Realizar una tarea simple en un solo paso.",
                "B": "Encadenar varios pasos donde uno activa al siguiente (efecto dominó).",
                "C": "No tener movimiento.",
                "D": "Solo usar electricidad."
            },
            "answer": "B"
        },
        {
            "id": 24,
            "type": "interpretativa",
            "topic": "Excel",
            "difficulty": "media",
            "text": "En Excel, =MAX(A1:A10) devuelve:",
            "choices": {
                "A": "La suma de las celdas A1 a A10.",
                "B": "El valor más alto del rango A1:A10.",
                "C": "El promedio del rango.",
                "D": "El número de celdas vacías."
            },
            "answer": "B"
        },
        {
            "id": 25,
            "type": "argumentativa",
            "topic": "Energía",
            "difficulty": "media",
            "text": "¿Por qué los paneles solares son más eficientes en zonas con mucha radiación solar?",
            "choices": {
                "A": "Porque generan más energía cuando reciben más luz solar.",
                "B": "Porque son más baratos en zonas frías.",
                "C": "Porque solo funcionan de noche.",
                "D": "Porque la radiación los daña y reduce su costo."
            },
            "answer": "A"
        }
    ],
    "grade9": [
        {
            "id": 21,
            "type": "propositiva",
            "topic": "Organizadores gráficos",
            "difficulty": "media",
            "text": "Para comparar las características de tres sistemas operativos, el organizador más adecuado es:",
            "choices": {
                "A": "Una matriz o tabla comparativa.",
                "B": "Un solo gráfico circular.",
                "C": "Una línea de tiempo.",
                "D": "Un mapa de Colombia."
            },
            "answer": "A"
        },
        {
            "id": 22,
            "type": "argumentativa",
            "topic": "Innovación",
            "difficulty": "media",
            "text": "¿Por qué muchas innovaciones surgen al observar problemas cotidianos?",
            "choices": {
                "A": "Porque los problemas reales revelan necesidades que pueden resolverse con soluciones nuevas.",
                "B": "Porque los problemas son siempre divertidos.",
                "C": "Porque no se requiere ningún análisis previo.",
                "D": "Porque las grandes ideas surgen sin observar el entorno."
            },
            "answer": "A"
        },
        {
            "id": 23,
            "type": "propositiva",
            "topic": "Inteligencia artificial",
            "difficulty": "media",
            "text": "Si vas a usar IA para resumir un texto largo, lo más responsable es:",
            "choices": {
                "A": "Confiar al 100% en el resumen sin leer el original.",
                "B": "Revisar el resumen contrastándolo con el texto original y citar la herramienta.",
                "C": "Publicar el resumen como propio sin verificar.",
                "D": "Pedirle inventar partes del texto."
            },
            "answer": "B"
        },
        {
            "id": 24,
            "type": "interpretativa",
            "topic": "Inteligencia artificial",
            "difficulty": "media",
            "text": "Un 'sesgo' en una IA significa que:",
            "choices": {
                "A": "Trabaja sin energía.",
                "B": "Sus resultados pueden favorecer o discriminar injustamente debido a los datos con que se entrenó.",
                "C": "Habla muy rápido.",
                "D": "Solo funciona en inglés."
            },
            "answer": "B"
        },
        {
            "id": 25,
            "type": "comprension_texto",
            "topic": "Evolución de la tecnología",
            "difficulty": "media",
            "text": "Lee: 'Cada salto tecnológico (escritura, imprenta, electricidad, internet) cambió la forma en que las personas trabajan, aprenden y se comunican.' Una conclusión válida es:",
            "choices": {
                "A": "La tecnología solo afecta el trabajo, no la vida diaria.",
                "B": "Los grandes saltos tecnológicos transforman varios aspectos de la sociedad.",
                "C": "La imprenta no fue importante.",
                "D": "Internet es el único cambio relevante."
            },
            "answer": "B"
        }
    ],
    "grade10": [
        {
            "id": 21,
            "type": "argumentativa",
            "topic": "Organizadores gráficos",
            "difficulty": "media",
            "text": "¿Por qué un diagrama de Gantt es útil en la gestión de proyectos?",
            "choices": {
                "A": "Porque muestra tareas con sus fechas de inicio y fin sobre una línea de tiempo, facilitando el seguimiento.",
                "B": "Porque reemplaza al equipo de trabajo.",
                "C": "Porque no requiere planificación previa.",
                "D": "Porque solo sirve para una persona."
            },
            "answer": "A"
        },
        {
            "id": 22,
            "type": "interpretativa",
            "topic": "Google Apps Script",
            "difficulty": "media",
            "text": "Un 'trigger' (disparador) en Apps Script permite:",
            "choices": {
                "A": "Cerrar la cuenta de Google.",
                "B": "Ejecutar una función automáticamente al ocurrir un evento (al abrir, al editar, por tiempo).",
                "C": "Cambiar el tema visual de Drive.",
                "D": "Eliminar archivos sin permiso."
            },
            "answer": "B"
        },
        {
            "id": 23,
            "type": "propositiva",
            "topic": "Plan de negocios",
            "difficulty": "media",
            "text": "Para validar la idea de negocio antes de invertir, lo más recomendable es:",
            "choices": {
                "A": "Hacer un MVP / prototipo y probarlo con clientes reales.",
                "B": "Comprar maquinaria costosa de inmediato.",
                "C": "Producir 10.000 unidades sin probar.",
                "D": "Lanzar una campaña masiva antes de tener el producto."
            },
            "answer": "A"
        },
        {
            "id": 24,
            "type": "argumentativa",
            "topic": "Ofimática",
            "difficulty": "media",
            "text": "¿Por qué se recomienda usar validación de datos al construir formularios en Sheets?",
            "choices": {
                "A": "Para que solo se acepten datos válidos y evitar errores en el análisis.",
                "B": "Para hacer que el archivo pese más.",
                "C": "Para imprimir en color automáticamente.",
                "D": "Porque obliga al usuario a no escribir."
            },
            "answer": "A"
        },
        {
            "id": 25,
            "type": "interpretativa",
            "topic": "Algoritmos",
            "difficulty": "media",
            "text": "En programación, un ciclo 'mientras' (while) se ejecuta:",
            "choices": {
                "A": "Una sola vez.",
                "B": "Mientras la condición sea verdadera.",
                "C": "Solo si la condición es falsa.",
                "D": "Nunca."
            },
            "answer": "B"
        }
    ],
    "grade11": [
        {
            "id": 21,
            "type": "propositiva",
            "topic": "Orientación vocacional",
            "difficulty": "media",
            "text": "Si tienes dudas entre dos carreras, una acción útil es:",
            "choices": {
                "A": "Asistir a charlas, ferias universitarias y hacer entrevistas a profesionales de ambas.",
                "B": "Inscribirte en una al azar.",
                "C": "No hacer nada y esperar a graduarte.",
                "D": "Dejar la decisión solo a tu familia."
            },
            "answer": "A"
        },
        {
            "id": 22,
            "type": "argumentativa",
            "topic": "Proyecto de vida",
            "difficulty": "media",
            "text": "¿Por qué los hábitos diarios son clave en el cumplimiento de un proyecto de vida?",
            "choices": {
                "A": "Porque las pequeñas acciones constantes producen grandes resultados a largo plazo.",
                "B": "Porque los hábitos no importan, solo los grandes eventos.",
                "C": "Porque hacen perder tiempo.",
                "D": "Porque obligan a vivir igual cada día sin metas."
            },
            "answer": "A"
        },
        {
            "id": 23,
            "type": "interpretativa",
            "topic": "Algoritmos",
            "difficulty": "media",
            "text": "Un 'arreglo' o 'lista' en programación es:",
            "choices": {
                "A": "Un único valor con nombre.",
                "B": "Una colección ordenada de varios valores accesibles por índice.",
                "C": "Una contraseña encriptada.",
                "D": "El sistema operativo del programa."
            },
            "answer": "B"
        },
        {
            "id": 24,
            "type": "propositiva",
            "topic": "Ofimática",
            "difficulty": "media",
            "text": "Para generar un certificado personalizado a 200 estudiantes con su nombre y código, lo más eficiente es:",
            "choices": {
                "A": "Escribir cada certificado a mano.",
                "B": "Usar combinación de correspondencia con una base de datos en Sheets/Excel.",
                "C": "Imprimir 200 certificados idénticos.",
                "D": "Pedir a cada estudiante que llene el suyo."
            },
            "answer": "B"
        },
        {
            "id": 25,
            "type": "interpretativa",
            "topic": "HTML",
            "difficulty": "media",
            "text": "En HTML, la etiqueta <img> sirve para:",
            "choices": {
                "A": "Insertar una imagen indicando su ruta con el atributo src.",
                "B": "Crear un encabezado.",
                "C": "Definir un enlace.",
                "D": "Insertar un párrafo."
            },
            "answer": "A"
        }
    ]
}


def main():
    for grade, new_qs in NEW.items():
        path = EXAMS / f"{grade}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        existing_ids = {q["id"] for q in data}
        added = 0
        for nq in new_qs:
            if nq["id"] in existing_ids:
                continue
            data.append(nq)
            added += 1
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{grade}: total {len(data)} (+{added} nuevas)")


if __name__ == "__main__":
    main()
