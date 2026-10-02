# CL Irrigation

Custom integration Home Assistant per la gestione intelligente dell'irrigazione.

## Versione 0.2.6

CL Irrigation gestisce cicli di irrigazione multi-zona con controllo automatico basato su umidita del terreno e previsioni meteo.

### Funzioni principali

- Da 1 a 8 zone di irrigazione.
- Pompa irrigazione opzionale con ritardi ON/OFF configurabili.
- Sensore umidita generale opzionale e sensore dedicato per ogni zona.
- Durata base 1-15 minuti con correzione automatica in base all'umidita.
- Controllo meteo opzionale con soglia di pioggia prevista.
- Quattro programmi orari automatici indipendenti.
- Avvio e arresto manuale del ciclo.
- Dashboard dinamica CL Irrigation con viste Centralina, Stato, Impostazioni e Storico.
- Grafici dell'umidita e dell'attivita delle valvole.
- Supporto italiano e inglese.

## Installazione manuale

1. Copia `custom_components/cl_irrigation` nella cartella `/config/custom_components/` di Home Assistant.
2. Riavvia Home Assistant.
3. Vai in **Impostazioni -> Dispositivi e servizi -> Aggiungi integrazione**.
4. Cerca **CL Irrigation** e completa la configurazione guidata.
5. Per la dashboard vai in **Impostazioni -> Plance -> Aggiungi plancia** e scegli **CL Irrigation** tra le Community dashboards.

## Installazione con HACS

Il repository e predisposto per l'installazione come repository personalizzato HACS di tipo **Integration**.

## Versione 0.2.6 - Storico

La dashboard dinamica include una quarta vista **Storico** con:

- andamento dell'umidita terreno per zona negli ultimi 7 giorni;
- attivita del ciclo e delle valvole nelle ultime 48 ore;
- ultimo ciclo, prossima partenza e durata totale prevista.

I sensori umidita per-zona sono predisposti per le statistiche a lungo termine di Home Assistant. Se una zona usa il sensore generale, il relativo sensore CL Irrigation continua a riflettere quel valore; quando viene assegnato un sensore dedicato alla zona, la dashboard usa automaticamente il nuovo valore.

## Autore

CL Impianti
