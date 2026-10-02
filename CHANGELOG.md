# Changelog

## 0.2.6
- Aggiunta nuova vista dinamica **Storico** alla dashboard CL Irrigation.
- Grafico statistiche dell'umidità terreno degli ultimi 7 giorni, separato per zona.
- Grafico attività delle ultime 48 ore con ciclo irrigazione e stato delle valvole.
- Riepilogo storico con ultimo ciclo, prossima partenza e durata prevista.
- I sensori di umidità creati da CL Irrigation ora espongono `device_class: humidity` e `state_class: measurement`, consentendo le statistiche a lungo termine di Home Assistant.
- Nessuna modifica alla logica di irrigazione o alle impostazioni esistenti.

## 0.2.5
- Durata base zone limitata a 1-15 minuti.

## 0.2.4
- Restyling della dashboard con programmi e zone separati in sezioni dedicate.
