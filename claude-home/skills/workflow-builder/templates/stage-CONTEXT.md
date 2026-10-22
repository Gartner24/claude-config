<!-- follows icm-architect e16cafe6a664dcf6d787a726b452adba77d913f4 -->
# NN_{{stage}}

{{One sentence: what this stage does in the pipeline.}}

Model: {{haiku|sonnet|opus}} {{low|medium|high}}

`<run>` below is `<repo>/.workflow/runs/{{name}}/<run id>`; the prompt gives you both values.

## Inputs
- `<run>/{{NN-1}}_{{earlier stage}}/output/{{file}}`: {{what it holds}}
- `{{an exact repo or ~/.claude path}}`: {{why this stage needs it}}

## Process
1. {{step}}
2. {{step}}
3. Write the outputs below, then return the schema the prompt names.

## Outputs
- `<run>/NN_{{stage}}/output/{{file}}`: {{what it holds}}

## Human check
{{The one thing the owner reads in the output after the run.}}

## Do NOT load
- {{files and folders this stage must not read, so its context stays small}}
