<p align="center">
  <img src="custom_components/cl_irrigation/brand/logo.png" alt="CL Irrigation" width="180">
</p>

<h1 align="center">CL Irrigation</h1>

<p align="center">
  Centralina di irrigazione intelligente per Home Assistant, sviluppata da <strong>CL Impianti</strong>.
</p>

<p align="center">
  <a href="https://github.com/climpianti/CL-Irrigation/releases/latest"><img src="https://img.shields.io/github/v/release/climpianti/CL-Irrigation?display_name=tag&style=flat-square" alt="Latest release"></a>
  <a href="https://github.com/climpianti/CL-Irrigation/releases"><img src="https://img.shields.io/github/downloads/climpianti/CL-Irrigation/total?style=flat-square" alt="Downloads"></a>
  <a href="https://github.com/climpianti/CL-Irrigation/issues"><img src="https://img.shields.io/github/issues/climpianti/CL-Irrigation?style=flat-square" alt="Issues"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2026.5%2B-41BDF5?style=flat-square&logo=homeassistant&logoColor=white" alt="Home Assistant 2026.5+">
  <img src="https://img.shields.io/badge/HACS-Custom%20Repository-41BDF5?style=flat-square" alt="HACS custom repository">
</p>

---

## Panoramica

**CL Irrigation** è una custom integration per Home Assistant pensata per gestire impianti di irrigazione a più zone attraverso valvole, pompa, sensori di umidità del terreno e previsioni meteo.

La configurazione avviene interamente dall'interfaccia di Home Assistant e l'integrazione genera una dashboard dinamica dedicata per controllo, programmazione, diagnostica e storico.

> **Versione corrente:** 0.2.6  
> **Home Assistant minimo:** 2026.5.0  
> **Lingue:** Italiano, English

## Funzioni principali

| Funzione | Descrizione |
|---|---|
| Zone irrigazione | Da **1 a 8 zone** configurabili |
| Valvole | Una valvola Home Assistant per ogni zona |
| Pompa | Opzionale, con ritardo di accensione e spegnimento |
| Umidità terreno | Sensore generale oppure sensore dedicato per ogni zona |
| Durata base | Regolabile da **1 a 15 minuti** per zona |
| Durata dinamica | Correzione automatica in base all'umidità del terreno |
| Meteo | Blocco automatico in base alla pioggia prevista |
| Programmi | **4 programmi orari** indipendenti |
| Avvio manuale | Avvio del ciclo dalla dashboard |
| STOP | Arresto immediato, chiusura valvole e spegnimento pompa |
| Dashboard | Centralina, Stato, Impostazioni e Storico |
| Storico | Grafici umidità e attività irrigazione |
| Statistiche | Sensori umidità compatibili con statistiche a lungo termine |

## Logica di irrigazione

Per ogni zona CL Irrigation calcola la durata effettiva partendo dalla durata base configurata.

In presenza di un sensore di umidità, il tempo viene adattato in base alle soglie impostate:

- terreno sufficientemente umido → irrigazione della zona bloccata;
- terreno normale → fattore standard;
- terreno secco → durata aumentata;
- terreno molto secco → durata ulteriormente aumentata.

Se una zona dispone di un sensore dedicato viene utilizzato quel valore. In caso contrario viene usato il sensore generale, se configurato.

Il controllo meteo può inoltre impedire l'avvio del ciclo quando la quantità di pioggia prevista supera la soglia configurata.

## Dashboard CL Irrigation

L'integrazione include una **Community Dashboard Strategy** dinamica basata esclusivamente su card native di Home Assistant.

### Centralina

La vista principale è progettata per l'uso quotidiano e mostra:

- stato dell'automazione;
- possibilità di irrigare;
- stato del sistema;
- zona attiva;
- prossimo avvio;
- durata totale prevista;
- comandi **Avvia ciclo** e **STOP**;
- quattro programmi automatici;
- controllo sintetico di ogni zona.

### Stato

La vista tecnica raccoglie:

- stato del ciclo;
- tempo rimanente;
- ultimo ciclo;
- meteo;
- umidità per zona;
- fattore applicato;
- durata calcolata;
- stato delle valvole.

### Impostazioni

Consente di regolare rapidamente:

- soglia pioggia;
- soglie di umidità;
- fattori di correzione;
- ritardi pompa;
- comportamento dell'avvio manuale;
- durata base delle zone.

### Storico

La versione 0.2.6 aggiunge:

- grafico dell'umidità terreno per zona negli ultimi **7 giorni**;
- storico di ciclo e valvole nelle ultime **48 ore**;
- ultimo ciclo;
- prossimo avvio;
- durata totale prevista.

## Installazione con HACS

CL Irrigation è attualmente distribuita come **repository personalizzato HACS**.

1. Apri **HACS**.
2. Apri il menu in alto a destra.
3. Seleziona **Repository personalizzati / Custom repositories**.
4. Inserisci:

```text
https://github.com/climpianti/CL-Irrigation
```

5. Come categoria seleziona **Integration**.
6. Aggiungi il repository.
7. Cerca **CL Irrigation** in HACS.
8. Installa l'ultima versione disponibile.
9. Riavvia Home Assistant.

Dopo il riavvio:

1. vai in **Impostazioni → Dispositivi e servizi**;
2. seleziona **Aggiungi integrazione**;
3. cerca **CL Irrigation**;
4. completa la configurazione guidata.

## Installazione manuale

1. Scarica l'ultima release dalla pagina [Releases](https://github.com/climpianti/CL-Irrigation/releases).
2. Copia la cartella:

```text
custom_components/cl_irrigation
```

in:

```text
/config/custom_components/cl_irrigation
```

3. Riavvia Home Assistant.
4. Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**.
5. Cerca **CL Irrigation**.

## Creazione della dashboard

Dopo aver configurato l'integrazione:

1. vai in **Impostazioni → Plance**;
2. seleziona **Aggiungi plancia**;
3. scegli **CL Irrigation** tra le Community dashboards.

La dashboard viene generata automaticamente in base al numero di zone configurate.

## Configurazione richiesta

Per ogni impianto puoi configurare:

- nome della centralina;
- pompa opzionale;
- entità meteo opzionale;
- sensore umidità generale opzionale;
- numero di zone;
- nome di ogni zona;
- valvola associata;
- sensore umidità dedicato opzionale;
- durata base.

Non è necessario modificare file YAML per la configurazione ordinaria.

## Sicurezza operativa

Il comando **STOP** ha priorità sul ciclo in esecuzione: interrompe il ciclo, chiude le valvole e comanda lo spegnimento della pompa.

Se un programma automatico scatta mentre un ciclo è già in corso, non viene avviato un secondo ciclo sovrapposto.

## Aggiornamenti

Gli aggiornamenti vengono pubblicati nella sezione:

[**GitHub Releases**](https://github.com/climpianti/CL-Irrigation/releases)

Per l'elenco delle modifiche consulta il [CHANGELOG](CHANGELOG.md).

## Segnalazioni e supporto

Per problemi, anomalie o proposte di miglioramento usa la sezione:

[**GitHub Issues**](https://github.com/climpianti/CL-Irrigation/issues)

Quando segnali un problema è utile indicare:

- versione di Home Assistant;
- versione di CL Irrigation;
- numero di zone;
- eventuale errore presente nei log;
- screenshot della dashboard, se pertinente.

## Stato del progetto

CL Irrigation è in sviluppo attivo. La release **0.2.6** rappresenta la prima release pubblica del progetto.

Prima di utilizzare nuove versioni su impianti critici è consigliato provarle su un sistema di test o effettuare un backup di Home Assistant.

## Autore

**CL Impianti**  
Impianti elettrici, automazione e integrazione Home Assistant.

Repository: [github.com/climpianti/CL-Irrigation](https://github.com/climpianti/CL-Irrigation)

---

<p align="center">
  <strong>CL Irrigation</strong><br>
  Smart irrigation for Home Assistant
</p>
