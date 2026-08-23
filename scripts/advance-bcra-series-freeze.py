#!/usr/bin/env python3
from pathlib import Path

path = Path('series/validate_bcra.py')
text = path.read_text(encoding='utf-8')
text = text.replace('frozen twelve-Series BCRA tranche', 'frozen eighteen-Series BCRA tranche')
text = text.replace('len(entries) != 12', 'len(entries) != 18')
text = text.replace('requires exactly 12 Series', 'requires exactly 18 Series')
text = text.replace('}) != 12', '}) != 18')
text = text.replace('map twelve distinct CanonicalIndicators', 'map eighteen distinct CanonicalIndicators')
text = text.replace('validated 12 authentic BCRA Series captures', 'validated 18 authentic BCRA Series captures')
path.write_text(text, encoding='utf-8')
print('Advanced BCRA integrity freeze from 12 to 18 Series.')
