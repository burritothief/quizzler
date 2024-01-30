from pathlib import Path

import click
from jinja2 import Environment, PackageLoader

import quizzler
from quizzler.config import config
from quizzler.quizzler import SATQuestion, set_uniform_underscore_length, tex_escape


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    env = Environment(
        loader=PackageLoader(quizzler.__name__, config.TEMPLATES_FOLDER),
        block_start_string="<BLOCK>",
        block_end_string="</BLOCK>",
        variable_start_string="<VAR>",
        variable_end_string="</VAR>",
        comment_start_string="<COMMENT>",
        comment_end_string="</COMMENT>",
    )
    env.filters["tex_escape"] = tex_escape
    env.filters["set_uniform_underscore_length"] = set_uniform_underscore_length
    ctx.obj["env"] = env


@cli.command()
@click.pass_context
def stats(ctx):
    pass


@cli.command()
def test():
    click.echo(quizzler.__name__)


@cli.command()
@click.pass_context
def generate(ctx):
    env = ctx.obj["env"]

    questions = SATQuestion.from_directory(Path("./question-bank/barrons-2024/"))
    # questions = SATQuestion.from_file(
    #     Path("./question-bank/barrons-2024/rhetorical-analysis.json")
    # )
    print(len(questions))
    template = env.get_template("quiz.tex")

    with open("output/test1.tex", "w") as f:
        f.write(template.render(questions=questions))


if __name__ == "__main__":
    cli()
