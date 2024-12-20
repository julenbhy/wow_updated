#!/bin/bash

set -e

echo "This script should only be called by compile.sh."

# Input variables
INPUT_FILE="$1"        # Original filename
METHOD="$2"            # Method selected by the user

FILENAME=$(basename "$INPUT_FILE" .rs) # Filename without the path and extension
BUILDER="action-builder-component"

# Prepare the builder
cp "$BUILDER/Cargo_template.toml" "$BUILDER/Cargo.toml"

# Add the necessary dependencies to the builder
crate_names=$(grep -Eo 'use [a-zA-Z0-9_]+(::)?' "$INPUT_FILE" | awk '{print $2}' | sed 's/::$//' | sort | uniq)
pwd
echo "Detected dependencies: $crate_names"
for crate in $crate_names; do
  if ! grep -q "^$crate =" $BUILDER/Cargo.toml; then
    echo "Adding dependency $crate to Cargo.toml"
    if ! cargo add --manifest-path "$BUILDER/Cargo.toml" "$crate"; then
      echo "Failed to add crate '$crate'. It may not be compatible or required."
    fi
  else
    echo "Dependency $crate already added to Cargo.toml" 
  fi
done

# concat the "func" function from the input file to $BUILDER/src/lib.rs
cp "$BUILDER/src/lib_template.rs" "$BUILDER/src/lib.rs"
cat "$INPUT_FILE" >> "$BUILDER/src/lib.rs"

# Compile the file with the selected method feature
echo "Compiling with component parser"
cargo build --manifest-path ./"$BUILDER"/Cargo.toml --release --target wasm32-wasip2 --features "$METHOD"

# Check if the compilation was successful
if [ $? -ne 0 ]; then
    echo "Compilation failed."
    exit 1
fi

mkdir -p "actions/compiled"

# Compile the WASM to a .cwasm file
$WASMTIME compile "target/wasm32-wasip2/release/action_component.wasm" -o "./actions/compiled/$FILENAME.cwasm"

# Package the .cwasm file into a zip
zip "./actions/compiled/$FILENAME.zip" "./actions/compiled/$FILENAME.cwasm"

# Deploy to OpenWhisk
wsk action update --kind wasm:0.1 "$FILENAME" "./actions/compiled/$FILENAME.zip"

echo "Action '$FILENAME' updated with parser '$PARSER'."
