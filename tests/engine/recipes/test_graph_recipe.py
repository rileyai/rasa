from typing import Text

import pytest
from pathlib import Path

import rasa.shared.utils.io
from rasa.engine.exceptions import GraphSchemaException
from rasa.engine.graph import GraphSchema
from rasa.engine.recipes.graph_recipe import GraphV1Recipe
from rasa.engine.recipes.recipe import Recipe
from rasa.shared.data import TrainingType
import rasa.engine.validation


CONFIG_FOLDER = Path("data/test_config")
# Short config has a single node for each of train and predict; should be fast to test.
SHORT_CONFIG = CONFIG_FOLDER / "graph_config_short.yml"
# The graph config is equivalent to the default config in graph schema format.
GRAPH_CONFIG = Path("rasa/engine/recipes/config_files/graph_config.yml")


def test_recipe_for_name():
    recipe = Recipe.recipe_for_name("graph.v1")
    assert isinstance(recipe, GraphV1Recipe)


@pytest.mark.parametrize(
    "config_path, expected_train_schema_path, expected_predict_schema_path, "
    "training_type",
    [
        (
            GRAPH_CONFIG,
            "data/graph_schemas/default_config_train_schema.yml",
            "data/graph_schemas/default_config_predict_schema.yml",
            TrainingType.END_TO_END,
        ),
        (
            SHORT_CONFIG,
            "data/graph_schemas/graph_config_short_train_schema.yml",
            "data/graph_schemas/graph_config_short_predict_schema.yml",
            TrainingType.BOTH,
        ),
        (
            SHORT_CONFIG,
            "data/graph_schemas/graph_config_short_train_schema.yml",
            "data/graph_schemas/graph_config_short_predict_schema.yml",
            TrainingType.NLU,
        ),
        (
            SHORT_CONFIG,
            "data/graph_schemas/graph_config_short_train_schema.yml",
            "data/graph_schemas/graph_config_short_predict_schema.yml",
            TrainingType.CORE,
        ),
    ],
)
def test_generate_graphs(
    config_path: Text,
    expected_train_schema_path: Text,
    expected_predict_schema_path: Text,
    training_type: TrainingType,
):
    expected_schema_as_dict = rasa.shared.utils.io.read_yaml_file(
        expected_train_schema_path
    )
    expected_train_schema = GraphSchema.from_dict(expected_schema_as_dict)

    expected_schema_as_dict = rasa.shared.utils.io.read_yaml_file(
        expected_predict_schema_path
    )
    expected_predict_schema = GraphSchema.from_dict(expected_schema_as_dict)

    config = rasa.shared.utils.io.read_yaml_file(config_path)

    recipe = Recipe.recipe_for_name(GraphV1Recipe.name)
    model_config = recipe.graph_config_for_recipe(
        config, {}, training_type=training_type
    )

    assert model_config.train_schema == expected_train_schema
    assert model_config.predict_schema == expected_predict_schema

    rasa.engine.validation.validate(model_config)


def test_language_returning():
    config = rasa.shared.utils.io.read_yaml(
        """
    language: "xy"
    recipe: graph.v1

    train_schema:
      nodes: {}
    predict_schema:
      nodes: {}
    """
    )

    recipe = Recipe.recipe_for_name(GraphV1Recipe.name)
    model_config = recipe.graph_config_for_recipe(config, {})

    assert model_config.language == "xy"


def test_retrieve_via_invalid_module_path():
    with pytest.raises(GraphSchemaException):
        path = "rasa.core.policies.ted_policy.TEDPolicy1000"
        GraphV1Recipe().graph_config_for_recipe(
            {
                "train_schema": {"nodes": {"some_graph_node": {"uses": path}}},
                "predict_schema": {},
            },
            cli_parameters={},
            training_type=TrainingType.CORE,
        )


def test_cli_parameter_warns():
    with pytest.warns(
        UserWarning, match="Graph Recipe does not utilize CLI parameters"
    ):
        GraphV1Recipe().graph_config_for_recipe(
            {"train_schema": {"nodes": {}}, "predict_schema": {"nodes": {}}},
            cli_parameters={"num_threads": 1, "epochs": 5},
            training_type=TrainingType.BOTH,
        )


def test_is_finetuning_warns():
    with pytest.warns(
        UserWarning, match="Graph Recipe does not utilize CLI parameters"
    ):
        GraphV1Recipe().graph_config_for_recipe(
            {"train_schema": {"nodes": {}}, "predict_schema": {"nodes": {}}},
            cli_parameters={},
            training_type=TrainingType.BOTH,
            is_finetuning=True,
        )
