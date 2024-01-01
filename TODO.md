Añadirle mejores tests
Añadirle CI/CD para que si no pasan los tests, no te deje ahcer el push
Esconder claves en secrets
Surf forecast desglosarlo en horas, Sacar datos de content de sforecast, cuando despliegas
TODO: quitar el sleep(10) de multithread y buscar otra alternativa para que no me baneen
Refactorizar
Cambiar poalrs por shapelets
Hacer algo para no tener tantos mains
Hacer que sea lo más visual posible, mapa de viento quizás
Ponerle mareas, subiendo o bajando en la tabla
ponerle el concurrent.futures.ThreadPoolExecutor para los selenium a la vez y mirar el consumo de recursos siguiendo las guias de streamlit
(https://blog.streamlit.io/3-steps-to-fix-app-memory-leaks/, https://blog.streamlit.io/common-app-problems-resource-limits/)
Cambiar pip por poetry
Meterle pydantic
Probar algún profiler, para trastear
Meterle windycom

Ponerle los plenos (cuando a todas horas del día las condiciones son buenas), o medios plenos, etc, Poner algo que diga dias con plenos, dependiendo de la pagina
TODO: arreglar surfline

TODO: notificaciones telegram p.ej cuando hay 1500 en playa de la cera, cuando hay viento solo sur o oeste en caleta caballo, cuando en la santa hay 100 o menos, cuando hay viento norte y +1000 en arrieta, punta
TODO: en la marea generar la tabla entera de 1 mes, sumandole 6h12.5

TODO: Refactorizar alertas en front/table
TODO: Captura de las distintas páginas cuando hay olas