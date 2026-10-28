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

## Rigenerare i mockup

```
python3 composite.py grafica.png retro.jpg fronte.jpg cartella_output/
```

Le coordinate in `composite.py` sono calibrate sulle foto originali 1066×1600 della felpa.
