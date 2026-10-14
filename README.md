# Gymchis

Web app de rutinas de gimnasio pensada para el iPhone: un cuestionario corto (objetivo, zonas, nivel, casa o gimnasio, equipo, días y minutos) arma una semana de entrenos con calentamiento, ejercicios y estiramientos. Durante el entreno muestra la animación de cada ejercicio, cuenta series y repeticiones, anota los kilos y lleva el cronómetro de trabajo y descanso.

**Abrir:** https://chumchis.github.io/gymchis/
En el iPhone: Safari → Compartir → *Agregar a pantalla de inicio*.

El progreso se guarda solo en el navegador del dispositivo.

## Datos

Los 1323 ejercicios y sus animaciones vienen de [ExerciseGymGifsDB](https://github.com/JahelCuadrado/ExerciseGymGifsDB) (v1.2.0, servidos por jsDelivr). Cada uno tiene nivel: **Principiante**, **Habitual**, **Experto** o **Coach**. Todos tienen nombre en español traducido a mano desde el original en inglés (`names_es.txt`; los 215 curados, en `build.py`) e instrucciones de técnica propias de 2 a 4 pasos (`instrucciones_es.txt`). Los curados también tienen nivel y tipo puestos a mano; para el resto `build.py` los deduce del nombre, el equipo y la categoría.

El generador usa todo el catálogo: prioriza el nivel de la persona y el anterior, da el doble de peso a los curados y, en casa, reparte los ejercicios entre su equipo (peso corporal, mancuernas, cuerda, bandas…) para que ninguno quede tapado.

## Desarrollo

```bash
python3 build.py   # regenera catalog.json (y img/ para la copia en claude.ai; necesita gif2webp)
node check.mjs     # prueba el generador de rutinas
```
