<!--
Project: FHS (Feature Hypotheses Simulation)
Copyright: Eifel42 Stefan Zils 2026
License: See LICENSE and README.md
#
Disclaimer: This software is provided "as is", without warranty of any kind,
express or implied, including but not limited to the warranties of
merchantability, fitness for a particular purpose, and noninfringement.
In no event shall the authors or copyright holders be liable for any claim,
damages or other liability, whether in an action of contract, tort or
otherwise, arising from, out of or in connection with the software or the
use or other dealings in the software.

-->

# DDD Architecture Tests (ArchUnit-Style)

Diese Tests sichern die Schichtgrenzen im `fhs`-Package automatisiert ab.

## Was wird geprüft?

- Import-Regeln zwischen Schichten (`domain_model`, `domain_service`, `application`, `infrastructure`, `presentation`).
- "Freeze"-Mechanik für bekannte Altlasten:
  - Bestehende Verletzungen sind explizit in `KNOWN_VIOLATIONS`.
  - Neue Verletzungen brechen den Test sofort.
- Repository-Contract als `typing.Protocol` im Domain-Layer.

## Warum das wie ArchUnit/jMolecules ist

- **ArchUnit-ähnlich:** Architekturregeln werden als ausführbare Tests formuliert.
- **jMolecules-ähnlich:** DDD-Stereotype werden als Domain-Konventionen geprüft
  (z. B. Repository als Domain-Contract/Protocol).

## Pflege

Wenn ein bestehender Verstoß behoben wurde:

1. Test laufen lassen.
2. Die gemeldeten "Resolved frozen violations" aus `KNOWN_VIOLATIONS` entfernen.

Wenn ein neuer Verstoß bewusst temporär akzeptiert wird:

1. Technische Schuld dokumentieren.
2. Erst dann den Eintrag in `KNOWN_VIOLATIONS` ergänzen.

Ziel: Die Freeze-Liste kontinuierlich verkleinern, bis die Regeln vollständig ohne Ausnahmen gelten.
