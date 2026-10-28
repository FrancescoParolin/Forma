# 0123456789 × ASAPROJECT — grafica felpa

Felpa nera collab tra due brand: resta tutto quello che c'è già sulla felpa
(`0123456789` bianco sul retro e piccolo sul petto) e si aggiunge
**ASAPROJECT** con il mood della scritta "MASSIVE" di riferimento: lettere
3D rosa gonfie e lucide, terminali a goccia, alone "peloso" fucsia sui bordi.

## Posizionamento

| Lato   | Cosa resta                       | Cosa si aggiunge                                                  |
|--------|----------------------------------|-------------------------------------------------------------------|
| Retro  | `0123456789` bianco, alto        | ASAPROJECT grande, subito sotto, centrato, ~20% più largo dei numeri |
| Fronte | `0123456789` piccolo, petto sx   | ASAPROJECT piccolo sul petto dx, stessa altezza (logo a specchio)  |

- `mockup_retro.jpg`, `mockup_fronte.jpg`: grafica applicata sulle foto reali della felpa.
- `grafica_v2_fluida_anteprima.png`: versione scelta (più vicina a MASSIVE).
- `grafica_v1_drip_anteprima.png`: alternativa più "slime/drip" con riccioli a fiamma.

Le anteprime qui sono a bassa risoluzione: questo ambiente scarica da Canva solo
le miniature. I file a piena risoluzione sono su Canva:

| File                         | Canva                                   |
|------------------------------|-----------------------------------------|
| Grafica v2 (fluida) su nero  | https://www.canva.com/M/MAHZVrcPF-4     |
| Grafica v1 (drip) su nero    | https://www.canva.com/M/MAHZVmCxaj4     |
| Mockup AI retro (v2)         | https://www.canva.com/M/MAHZVqLxn9E     |
| Mockup AI fronte (v2)        | https://www.canva.com/M/MAHZVrc5lCQ     |
| Mockup AI retro (v1)         | https://www.canva.com/M/MAHZVkcfIdU     |
| Mockup AI fronte (v1)        | https://www.canva.com/M/MAHZVi33gbQ     |

I mockup AI ridisegnano il testo: prima di usarli, controllare a piena
risoluzione che "ASAPROJECT" e "0123456789" siano scritti giusti.

## Note per la stampa

- La grafica è su fondo nero puro: per la stampa serve scontornarla
  (PNG trasparente). L'alone "peloso" va mantenuto nel file di stampa, non tagliato.
- L'effetto 3D lucido e l'alone sfumato sono sfumature fotografiche: la tecnica
  (DTG, DTF o serigrafia a retino) va decisa con lo stampatore.

## Prove di sovrapposizione (`sovrapposizione/`)

Le due scritte incrociate invece che una sotto l'altra, sulla foto originale
della felpa. I numeri restano sopra il rosa, bianchi e senza bordo.

| File                              | Trattamento                                                    |
|-----------------------------------|----------------------------------------------------------------|
| `retro_B_numeri_al_centro.jpg`    | numeri al centro di ASAPROJECT                                 |
| `retro_D_numeri_in_alto.jpg`      | rosa più in basso, i numeri tagliano la parte alta delle lettere |
| `retro_G_numeri_sulle_gocce.jpg`  | rosa più in alto, i numeri passano sulle gocce                 |
| `retro_I_intreccio.jpg`           | tre aste rosa ripassano sopra i numeri                         |
| `retro_G_finale.jpg`              | **scelta**: G con il rosa all'87%, tutto dentro le spalle      |
| `fronte_sovrapposto.jpg`          | logo piccolo sul petto, i numeri passano sulle gocce           |

G è stata confermata da tre valutazioni indipendenti (impatto streetwear,
leggibilità dei due brand, stampa) e da una verifica critica: è l'unica in
cui si leggono per intero sia tutte le cifre sia tutte le lettere. Nella G
originale la A e la T uscivano dalle spalle; in `retro_G_finale.jpg` il rosa
è ridotto all'87% attorno alla base delle lettere e sta tutto dentro la
sagoma (verificato sui pixel, con 7 px di margine). Senza bordo, l'intreccio
(I) fa sembrare le cifre interrotte: è la prova più debole.

## Rigenerare i mockup

```
python3 composite.py grafica.png retro.jpg fronte.jpg cartella_output/
```

Per le sovrapposizioni:

```
python3 overlap.py grafica.png retro.jpg cartella_output/
python3 overlap_front.py grafica.png fronte.jpg output.jpg 120 -12 0   # larghezza, spostamento verticale, bordo
```

Le coordinate negli script sono calibrate sulle foto originali 1066×1600 della felpa.
