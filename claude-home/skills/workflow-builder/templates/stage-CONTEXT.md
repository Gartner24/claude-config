<!-- follows icm-architect 8bc2f5610d3843b3ffa31a142effe6b6337fef3c -->
# NN_{{stage}}

{{One sentence: what this stage does in the pipeline.}}

Model: {{haiku|sonnet|opus}} {{low|medium|high}}

`<run>` below is `<repo>/.workflow/runs/{{name}}/<run id>`; the prompt gives you both values.

## Inputs
- `<run>/{{NN-1}}_{{earlier stage}}/output/{{file}}`: {{what it holds}}
- `{{an exact repo or ~/.claude path}}`: {{why this stage needs it}}

## Process
1. If an input is missing or empty, stop and say which.
2. {{step}}
3. {{step}}
4. Write the outputs below, then return the schema the prompt names.

## Outputs
- `<run>/NN_{{stage}}/output/{{file}}`: {{what it holds}}

## Check
{{Who or what checks, as one act: the owner reads X / a script confirms Y / a small model answers Z; a check that is not a person writes check.md beside the output, first line pass or fail: <why>.}}

## Do NOT load
- {{files and folders this stage must not read, so its context stays small}}
