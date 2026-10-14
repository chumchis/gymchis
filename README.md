# Gymchis

Web app de rutinas de gimnasio pensada para el iPhone: un cuestionario corto (objetivo, zonas, nivel, casa o gimnasio, equipo, días y minutos) arma una semana de entrenos con calentamiento, ejercicios y estiramientos. Durante el entreno muestra la animación de cada ejercicio, cuenta series y repeticiones, anota los kilos y lleva el cronómetro de trabajo y descanso.

**Abrir:** https://chumchis.github.io/gymchis/
En el iPhone: Safari → Compartir → *Agregar a pantalla de inicio*.

El progreso se guarda solo en el navegador del dispositivo.

## Datos

Los 1323 ejercicios y sus animaciones vienen de [ExerciseGymGifsDB](https://github.com/JahelCuadrado/ExerciseGymGifsDB) (v1.2.0, servidos por jsDelivr). El generador de rutinas usa 215 de ellos, curados a mano con nombres en español, nivel y tipo; el resto se puede ver en *Ejercicios* y elegir al cambiar un ejercicio.

## Desarrollo

```bash
python3 build.py   # regenera catalog.json (y img/ para la copia en claude.ai; necesita gif2webp)
node check.mjs     # prueba el generador de rutinas
```
