# recap

![build](https://github.com/georgw777/recap/workflows/build/badge.svg)

_Recap_ is a tool for providing _REproducible Configurations for Any Project_.

Research should be reproducible.
Especially in deep learning, it is important to keep track of hyperparameters and configurations used in experiments.
This package aims at making that easier.

## Installing

Just install like any Python package:

```bash
pip install recap
```

## Overview

Recap provides two top-level concepts that would be imported as follows:

```python
from recap import URI, CfgNode as CN
```

The `CfgNode` is a subclass of [yacs](https://github.com/rbgirshick/yacs)' `CfgNode`.
It provides some additional features for parsing configurations that are inherited between files which is not possible with [yacs](https://github.com/rbgirshick/yacs).

Recap's `URI` class provides a mechanism for handling logical paths within your project more conveniently with an interface that is fully compatible with `pathlib.Path`.

## YAML configurations

Configurations are defined [just like in yacs](https://github.com/rbgirshick/yacs#usage), except that you need to import the `CfgNode` class from the recap package instead of yacs.
Consider the following YAML configuration that sets default values for all configuration options we will use in our project. We shall name it `_base.yaml` because our experiments will build on these values.

```yaml
SYSTEM:
  NUM_GPUS: 4
  NUM_WORKERS: 2
TRAIN:
  LEARNING_RATE: 0.001
  BATCH_SIZE: 32
  SOME_OTHER_HYPERPARAMETER: 10
```

The equivalent configuration can be obtained programatically like so:

```python
from recap import CfgNode as CN

cfg = CN()
cfg.SYSTEM = CN()
cfg.SYSTEM.NUM_GPUS = 4
cfg.SYSTEM.NUM_WORKERS = 2
cfg.TRAIN = CN()
cfg.TRAIN.LEARNING_RATE = 1e-3
cfg.TRAIN.BATCH_SIZE = 32
cfg.TRAIN.SOME_OTHER_HYPERPARAMETER = 10

print(cfg)
```

### Inheriting configurations

Recap provides functionality for inheriting configuration options from other configuration files by setting the top-level `_BASE_` key.
So, we could create a configuration file `experiment_1.yaml` for an experiment where we try a different learning rate and batch size:

```yaml
_BASE_: _base.yaml

TRAIN:
  LEARNING_RATE: 1e-2
  BATCH_SIZE: 64
```

In our code, when we want to load the experiment configuration, we would use the `recap.CfgNode.load_yaml_with_base()` function:

```python
from recap import CfgNode as CN

cfg = CN.load_yaml_with_base("experiment_1.yaml")

print(cfg)

# Will output:
"""
SYSTEM:
  NUM_GPUS: 4
  NUM_WORKERS: 2
TRAIN:
  LEARNING_RATE: 0.01
  BATCH_SIZE: 64
  SOME_OTHER_HYPERPARAMETER: 10
"""
```

Note that the `_BASE_` keys can be arbitrarily nested; however, circular references are prohibited.

## Logical URIs and the path manager

Recap includes a path manager for conveniently specifying paths to logical entities.
The path strings are set up like a URI where the scheme (i.e. `http` in the path string `http://google.com`) refers to a logical entity.
Each such entity needs to be set up as a `PathTranslator` that can translate the logical URI path to a physical path on the file system.

For example, we could set up a path translator for the `data` scheme to refer to the the path of a dataset on our file system located at `/path/to/dataset`. Then the recap URI `data://train/abc.txt` would be translated to `/path/to/dataset/train/abc.txt`.

The simplest way of setting that up is using the `register_translator` function (although more complex setups are possible with the `recap.path_manager.PathTranslator` class, allowing you to download files from the internet, for example):

```python
from recap.path_manager import register_translator
from pathlib import Path

register_translator("data", Path("/path/to/dataset"))
```

Then, we can use the `recap.URI` class just like any `pathlib.Path` object:

```python
from recap import URI

my_uri = URI("data://train/abc.txt")
# Here, str(my_uri) == "/path/to/dataset/train/abc.txt"

with my_uri.open("r") as f:
    print(f.read())
```

### Logical URIs in inherited configurations

The `recap.URI` interface is fully compatible with the nested configurations.
This means that you can use recap `URI`s within the `_BASE_` field for inheriting configurations.

For example, you could register a path translator for the `config` scheme and then include `_BASE_: config://_base.yaml` in your configuration files.
