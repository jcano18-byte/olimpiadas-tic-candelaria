Proyecto: Olimpiadas de Tecnología e Informática

Contenido creado:
- exams/grade6.json ... grade11.json : bancos de 20 preguntas por grado (A-D, respuesta indicada).
- scripts/generate_simple_pdfs.py : script que genera PDFs simples desde los JSON (usa reportlab).

Siguientes pasos recomendados:
1. Revisar y ajustar preguntas según currículo local y estilo deseado.
2. Instalar dependencias: `pip install reportlab`.
3. Generar PDFs ejecutando:

```bash
python scripts/generate_simple_pdfs.py
```

4. Crear hoja de respuestas OMR (plantilla) y generar códigos únicos por estudiante.
5. Implementar el lector OMR y la integración con Google Sheets.

Si quieres, puedo:
- Ajustar preguntas (lenguaje o dificultad).
- Generar también la hoja OMR en PDF y un CSV con códigos por estudiante.
- Subir `students.csv` al repo si me das el listado.
