# GUION DE DEMOSTRACIÓN TÉCNICA - OPTIMAFLOW V1
*Documento de Cierre para Llamadas de Zoom / Presentaciones de Ventas*

---

> **Instrucción de Respuesta Rápida:**
> Si escribes en el chat "MODO DEMO [Sector]" (ej. "MODO DEMO Logística"), mi inteligencia reaccionará instantáneamente leyendo el CSV sucio de ese sector y escupiendo por terminal el reporte de anomalías financieras para que lo proyectes en pantalla.

---

## 1. SECTOR: REFACCIONES AUTOMOTRICES
*Data*: `demo_refacciones.csv`

**A. El Momento Aha! (El Dolor)**
> "Sabemos que manejan miles de SKUs con precios que fluctúan. Miren esta fila del reporte: El mostrador vendió 10 bujías de platino. El precio real es de $250 cada una, pero alguien tecleó equivocadamente $2.50. También veo un 'Quiebre de Stock Fantasma': están vendiendo balatas que el sistema dice que ya no tienen. Si esta sábana de Excel tiene un millón de celdas, este error pasa directo a contabilidad y perdieron mil pesos en un segundo."

**B. La Solución Agéntica**
> "Aquí es donde entra OptimaFlow. Nuestro agente vive como un middleware conectado a su punto de venta. No tienen que cambiar de software. OptimaFlow intercepta la tabla de Excel _antes_ de que cierre el día, detecta la incongruencia matemática entre el precio base y la facturación, y detiene la fuga enviando un webhook a su gerente por WhatsApp."

**C. El ROI**
> "Si tienen tan solo 10 errores de captura de este tipo a la semana a través de 5 sucursales, estamos hablando de una pérdida invisible conservadora de $50,000 MXN mensuales. OptimaFlow se paga solo en las primeras 48 horas de despliegue al detener estas fugas de capital."

---

## 2. SECTOR: LOGÍSTICA B2B / CEDIS
*Data*: `demo_logistica.csv`

**A. El Momento Aha! (El Dolor)**
> "En el andén la velocidad manda. Miren este registro de carga: su montacarguista embarcó 50 pallets de emplaye al tráiler, pero la factura y la orden de salida solo cobraron 5 pallets al cliente. Le acaban de regalar 45 tarimas de producto al destinatario. Es imposible auditar a mano cada guía de carga contra facturación al final del turno."

**B. La Solución Agéntica**
> "OptimaFlow cruza los datos del WMS (Warehouse Management) contra la facturación del ERP en milisegundos. Cuando ve que `Cant_Despachada (50)` no es igual a `Cant_Facturada (5)`, genera una anomalía crítica e impide la salida del camión hasta que el gerente valide la diferencia."

**C. El ROI**
> "Un solo camión mal auditado puede representar hasta $100,000 MXN en material no facturado. Al blindar la puerta de salida digitalmente, garantizamos que el 100% del inventario que sale del almacén, se convierte en flujo de caja."

---

## 3. SECTOR: DISTRIBUCIÓN DE ALIMENTOS
*Data*: `demo_alimentos.csv`

**A. El Momento Aha! (El Dolor)**
> "El gran enemigo de los perecederos es la caducidad. Para intentar sacar la mercancía próxima a vencer, sus vendedores de ruta aplican descuentos. Pero miren este registro: El yogurt con precio base de $15 se vendió a $1.50. El vendedor aplicó un descuento tan agresivo sin autorización que cruzaron el umbral de rentabilidad. Estuvieron operando con un margen negativo de -85% en ese lote entero."

**B. La Solución Agéntica**
> "OptimaFlow no duerme. Barre constantemente todas sus celdas de transacciones buscando márgenes de precio rotos. Si identifica que una matriz de venta bajó de su límite permitido, el agente aísla la venta y alerta a la dirección comercial para revisar la autorización."

**C. El ROI**
> "Sostener márgenes en alimentos es cuestión de vida o muerte para el negocio. Recuperar un 3% de rentabilidad a nivel macro simplemente auditando que ningún lote se remate por debajo del costo, suma millones de pesos anuales devueltos a su balance."

---
*Fin del Guion. Preparados para Cierre.*
