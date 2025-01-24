Añadirle mejores tests
Añadirle CI/CD para que si no pasan los tests, no te deje ahcer el push
Esconder claves en secrets
TODO: quitar el sleep(10) de multithread y buscar otra alternativa para que no me baneen
Refactorizar
Cambiar poalrs por shapelets
Hacer algo para no tener tantos mains
Cambiar pip por poetry
Meterle pydantic
Probar algún profiler, para trastear
Meterle windycom

Ponerle los plenos (cuando a todas horas del día las condiciones son buenas), o medios plenos, etc, Poner algo que diga dias con plenos, dependiendo de la pagina
TODO: arreglar surfline

TODO: notificaciones telegram p.ej cuando hay 1500 en playa de la cera, cuando hay viento solo sur o oeste en caleta caballo, cuando en la santa hay 100 o menos, cuando hay viento norte y +1000 en arrieta, punta
TODO: en la marea generar la tabla entera de 1 mes, sumandole 6h12.5
TODO: Porcentaje de marea

TODO: Refactorizar alertas en front/table
TODO: Captura de las distintas páginas cuando hay olas
TODO poner bajo risco, las conchas, montaña amarilla

# Crear nuevos spots que no aparecen en sforecast

# Si la fuerza no es oeste en el dataframe, que no muestre papagayo TODO

Refactorizar meet_x_conditions
Poner algun elemento a fixed para que no se expanda tanto hacia abajo la página

Migrar a scrapy
escrapear temperatura, precipitaciones
elegir qué campos quieres que se muestren en el dataframe
Poner la dirección bien, más oeste menos oeste, más este menos este ... Capturar los grados (fijar lo que es norte, sur, este y oeste puros y lo que más se acerque mejor, 0 grados norte, 90 es Este, 180 es sur, 270 es Oeste)
Añadirle tests de spots con tales condiciones a ver si me los marca
Meterle fecha y hora actual y donde hay
Arreglar el fallo donde se borra el caché
Eliminar codigo muerto
POner para clasificar en vacia o llena
Poner columna con dias que faltan 
poner tabla con el dia de hoy
switchear tabla a tabla a surf forecast
Refactorizar, tipar
TODO posiblemente hacer una clase para calcular los spot_names
Grafica con fuerza norte y otra con fuerza oeste