# Guion para el video: Máquina de Turing reconocedora

## 1. Propósito de la MT reconocedora

Nuestra máquina reconoce el lenguaje L = { w#w | w pertenece a {a, b}+ }. Esto significa que la entrada debe tener dos cadenas iguales, separadas por un numeral. Ambas deben tener las mismas letras, en el mismo orden, y cada lado debe tener al menos una letra.

La tarea de esta máquina es determinar si una cadena pertenece al lenguaje. Durante la comparación modifica la cinta para llevar el control de las letras que ya revisó.

## 2. Explicación de la arquitectura de la MT en el YAML

La configuración de la máquina está en este archivo YAML. Aquí definimos los estados, los alfabetos y las transiciones que indican qué hacer según el estado, la memoria y el símbolo que está leyendo el cabezal.

### 2.1. Qué significa una transición

Cada transición depende de tres datos: el estado actual, el contenido de la memoria caché y el símbolo que está leyendo el cabezal. La regla indica a qué estado pasar, qué guardar en memoria, qué escribir en la cinta y hacia dónde moverse. R significa derecha, L izquierda y S quedarse en la misma posición.

### 2.2. Cómo compara las dos partes

La máquina toma la primera letra pendiente del lado izquierdo, la guarda en la memoria caché y borra esa letra de la cinta. Después avanza hasta cruzar el numeral y busca la primera letra del lado derecho que todavía no esté marcada.

Si esa letra coincide con la que tiene guardada, escribe una X y regresa al lado izquierdo para repetir el proceso. Si encuentra una letra distinta o falta una letra, no hay una transición disponible y la cadena se rechaza.

Cuando termina el lado izquierdo, comprueba que a la derecha solo queden las X de las comparaciones anteriores. Si no sobran letras y se comparó al menos una pareja, llega al estado de aceptación.

### 2.3. Para qué sirve cada estado

Cada estado tiene una tarea dentro del recorrido. Los estados del cero al tres hacen la comparación de las letras, el cuatro verifica que no sobren letras a la derecha y el cinco indica aceptación. La verificación de al menos una X evita aceptar una entrada formada únicamente por el numeral.

## 3. Demostración de cadenas de prueba en el frontend

### 3.1. Qué muestra el simulador

La cinta nos permite seguir los cambios y ver dónde está el cabezal. También podemos revisar el estado y la memoria en cada paso. En la tabla de descripciones instantáneas, el estado aparece entre corchetes justo antes del símbolo que está leyendo el cabezal. Al seleccionar una fila, podemos volver a esa configuración.

### 3.2. Cómo interpretar el resultado

La cadena se acepta cuando la máquina llega al estado cinco. Si se detiene porque no tiene una transición disponible, se rechaza. El simulador también tiene un límite de pasos para detener ejecuciones demasiado largas. Si se alcanza ese límite, el resultado es indeterminado, por lo que no podemos presentarlo como un rechazo.

### 3.3. Ejemplos de la reconocedora

#### Demostración paso a paso: `ab#ab`

Aquí tenemos ab a ambos lados del numeral. La máquina guarda la primera a y la borra de la izquierda. Luego cruza el numeral, encuentra la otra a y la marca con X. Regresa por la b y repite el procedimiento. Cuando termina, revisa las dos X de la derecha y llega al estado cinco.

#### Casos incluidos en el YAML

Estos son los cuatro casos definidos en el YAML. Las primeras dos cadenas se aceptan porque sus mitades son iguales. En las otras dos encontramos diferencias durante la comparación y la máquina se detiene sin una transición disponible. Podemos abrir la última descripción instantánea para ver exactamente dónde ocurrió.

## 4. Pequeña conclusión de la MT

Con estas ejecuciones podemos ver cómo la máquina compara las letras en orden y revisa que no sobre ninguna. La cadena se acepta cuando ambos lados del numeral son iguales y tienen al menos una letra.
