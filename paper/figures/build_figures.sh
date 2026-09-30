#!/usr/bin/env bash
# Rebuilds every figure of the paper: UML diagrams (PlantUML -> SVG -> vector PDF) and data charts (matplotlib).
# Needs: java, graphviz (dot), librsvg2-bin (rsvg-convert), fonts-liberation, python3 with numpy and matplotlib.
#   apt-get install -y graphviz librsvg2-bin fonts-liberation && pip install matplotlib numpy
# Environment:
#   PLANTUML_JAR      path of plantuml-<version>.jar (downloaded from Maven Central to .cache/ when unset)
#   ASTRO_REPO        Android checkout that the charts read (default /home/user/astrofixer-baby/astrofixxer-android)
#   PLATESOLVER_XML   JUnit XML of PlateSolverTest (from `gradle test` in the JVM harness, see chart_solver.py)
#   RUN_JVM_HARNESS   directory of the JVM harness; when set, `gradle test --offline` is run there first
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="$here/src"
version="1.2025.4"
export ASTRO_REPO="${ASTRO_REPO:-/home/user/astrofixer-baby/astrofixxer-android}"

if [ -n "${RUN_JVM_HARNESS:-}" ]; then
  (cd "$RUN_JVM_HARNESS" && gradle test --offline)
  export PLATESOLVER_XML="$RUN_JVM_HARNESS/build/test-results/test/TEST-org.astrofixxer.astro.PlateSolverTest.xml"
fi

jar="${PLANTUML_JAR:-$here/.cache/plantuml-$version.jar}"
if [ ! -f "$jar" ]; then
  mkdir -p "$(dirname "$jar")"
  curl -sSfL -o "$jar" "https://repo1.maven.org/maven2/net/sourceforge/plantuml/plantuml/$version/plantuml-$version.jar"
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cd "$src"
for f in uml*.puml; do
  name="${f%.puml}"
  java -jar "$jar" -tsvg -o "$tmp" "$f"
  rsvg-convert -f pdf -o "$here/$name.pdf" "$tmp/$name.svg"
  echo "wrote figures/$name.pdf"
done

for c in chart_precession.py chart_solver.py chart_data.py; do
  echo "== $c"
  python3 "$src/$c"
done
