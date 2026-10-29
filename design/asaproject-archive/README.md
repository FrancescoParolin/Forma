# ASAPROJECT — felpa Archive / Military

Felpa nera lavata, oversize. Un solo emblema e un solo slogan, stampa crepata
sul retro e puff sul petto. Il bianco osso è il colore base; il rosa fluo è
l'unico accento ed è usato solo su "ASA".

| Elemento   | Scelta                                                        |
|------------|---------------------------------------------------------------|
| Wordmark   | ASAPROJECT stencil militare (nuovo, scelto dal cliente)       |
| Emblema    | Mirino con ASA rosa al centro, dentro un bordo di filo spinato |
| Slogan     | NOBODY GAVE US PERMISSION (maiuscolo condensato)              |
| Codice     | ASA-001 · EST. 2026 (nessuna città)                           |

## Mockup (`mockup/`)

- `mockup_retro.jpg`, `mockup_fronte.jpg`: la grafica è montata sulle foto
  originali della felpa, in scala reale (22 px per pollice, calibrati su
  tasca e polsino). Dalle foto sono stati tolti le stampe `0123456789`
  dell'altro brand, la linguetta laterale del retro e il nastro sul fianco
  del fronte. Il nero lavato è simulato.
- `dettaglio_*.jpg`: primi piani a risoluzione di stampa su jersey simulato
  (stampa crepata, mirino, filo spinato, puff del petto, codice sull'orlo).

## File di stampa (`stampa/`)

Lastre a 1 bit, 300 dpi, **nero = inchiostro su bianco** (positivo per pellicola).
Ogni lastra ha un margine di 0,25 in con segni di registro (mirini agli
angoli e tacche sulle linee di centro), identici su tutte le lastre dello
stesso set: servono solo per la pellicola, sul telaio vanno coperti.

| Posizione | Misura          | Lastre                                                       | Tecnica            |
|-----------|-----------------|--------------------------------------------------------------|--------------------|
| Retro     | 14 × 13,25 in   | `retro_0_sottofondo_bianco`, `retro_1_bone`, `retro_2_rosa_806C` | serigrafia crepata |
| Petto sx  | 3,5 × 3,5 in    | `petto_1_bone_puff`, `petto_2_rosa_806C_piatto`, `petto_0_sottofondo_bianco_sotto_rosa` | bone in puff, rosa piatto |
| Orlo      | 4,68 × 0,41 in  | `orlo_0_sottofondo_bianco`, `orlo_1_bone`                     | serigrafia piena   |

Posizioni nel mockup (da confermare sul capo reale con lo stampatore):
retro con la parte alta circa 2,7 in sotto il bordo del cappuccio abbassato,
centrato; codice centrato, con il centro 1,25 in sopra la cucitura del
polsino; petto con il centro a 4 in dal centro davanti, sul lato sinistro di
chi indossa.

`anteprima_stampa_*.png` sono anteprime a colori (RGBA, 300 dpi), non lastre.

### Regole di produzione rispettate (misurate sui file)

- Puff del petto: tratto minimo 1,6 mm, spazio minimo 2,58 mm, niente punte
  sottili (le punte del filo sono barre arrotondate). Il rosa è piatto, a
  2,5 mm dal puff, con il suo sottofondo.
- Crepe: celle da 4 a 10 mm, larghezza da 0,5 a 0,8 mm (si stringono a
  0,5 mm verso la fine, mai meno), circa 13% della superficie crepabile.
  Crepano solo i tratti oltre 3,2 mm (wordmark, anello esterno, bracci del
  mirino, ASA); filo, punte, anello interno, tacche, puntini, slogan e
  codice restano pieni. Nessuna crepa entro 3 mm dai ponti stencil, nessun
  trattino isolato o forellino.
- Nessun dettaglio d'inchiostro sotto 0,42 mm, nessun frammento di colore
  sotto 1 mm² e nessuna isola di colore senza sottofondo.
- Ponti stencil del wordmark di 3,4 mm (8% delle maiuscole) con spazi tra le
  lettere di 7 mm, così i pezzi di P, R, O, E restano raggruppati.
- Filo spinato: due fili da 2,5 mm che si incrociano sopra/sotto, 16 punte
  fatte di due fili tagliati in diagonale con un avvolgimento a spirale,
  punte a circa 9 mm dal filo, taglio netto a ore 1.
- Slogan largo esattamente quanto l'emblema (9,07 in), maiuscole 0,57 in.
- Sottofondo bianco ristretto di 0,17 mm sotto i colori; nessun pixel fuori.

### Da decidere con lo stampatore

- Pantone del bianco osso (`#E8E2D2` è solo il riferimento a schermo) con
  una prova di colore sul tessuto lavato; il rosa è pensato come Pantone 806 C.
- Telai, maglie, flash e prova di stampa (strike-off).
- Le lastre sono raster a 300 dpi, non vettoriali: se lo stampatore vuole
  file vettoriali vanno convertite.

## Font e originalità

- Wordmark: Inter Black (SIL Open Font License), ridisegnato a stencil.
- Slogan e codice: Barlow Condensed (SIL Open Font License,
  `sorgenti/fonts/OFL-Barlow.txt`), alla larghezza naturale.
- Tutti gli elementi sono costruiti da zero con forme generiche (mirino, filo
  spinato, stencil). Nelle revisioni non è emersa somiglianza con i marchi
  citati nel brief, ma non è una ricerca di anteriorità: prima di registrare
  il marchio conviene farla fare a un professionista.

## Rigenerare tutto

```
python3 sorgenti/mockup_archive.py sorgenti <cartella_foto_felpa> <cartella_output>
```

`<cartella_foto_felpa>` deve contenere `hoodie_back.jpg` e `hoodie_front.jpg`
(le foto originali 1066×1600). Servono Pillow, numpy e scipy.
