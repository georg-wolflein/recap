import os
from typing import Dict, Any
from pathlib import Path
from yacs.config import CfgNode as _CfgNode
import functools
import yaml

from .path_manager import URI

BASE_KEY = "_BASE_"


class CfgNode(_CfgNode):
    """A subclass of yacs' CfgNode that additionally implements inheritance of configuration files and is compatible with recap URIs.
    """

    def __init__(self, init_dict=None, key_list=None, new_allowed=False):
        def ensure_cfgnode(item):
            if isinstance(item, dict) and not isinstance(item, _CfgNode):
                return CfgNode(item)
            else:
                return item
        if init_dict is not None:
            init_dict = {key: value if not isinstance(value, list) else list(map(ensure_cfgnode, value))
                         for key, value in init_dict.items()}

        super().__init__(init_dict=init_dict, key_list=key_list, new_allowed=new_allowed)

    @classmethod
    def load_yaml_with_base(cls, filename: os.PathLike) -> "CfgNode":
        """Load a YAML configuration file that may inherit from other YAML files.

        Args:
            filename (os.PathLike): the path to the YAML file (can be a recap URI)

        Returns:
            CfgNode: the loaded configuration
        """

        uri = URI(filename)
        with uri.open("r") as f:
            cfg = cls.load_cfg(f)
        if BASE_KEY in cfg:
            base_cfg = cls.load_yaml_with_base(cfg[BASE_KEY])
            del cfg[BASE_KEY]
            base_cfg.merge_from_other_cfg(cfg)
            return base_cfg
        return cfg

    def merge_with_dict(self, overrides: Dict[str, Any]):
        """Merge a dict of configurations into this configuration object.

        The dict must contain string keys. 
        The configuration hierarchy is accessed using the "." delimiter.

        Args:
            overrides (Dict[str, Any]): the dict of configurations to merge (overwrite)
        """

        for key, value in overrides.items():
            child = self
            *path_segments, prop = key.split(".")
            for path_segment in path_segments:
                if path_segment not in child:
                    child[path_segment] = CfgNode()
                child = child[path_segment]
            child[prop] = value

    def dump(self, **kwargs):
        def convert_node(cfg_node):
            if isinstance(cfg_node, list):
                return [convert_node(v) for v in cfg_node]
            if isinstance(cfg_node, dict):
                return {k: convert_node(v) for k, v in cfg_node.items()}
            else:
                return cfg_node
        return yaml.safe_dump(convert_node(self), **kwargs)

    def params_dict(self) -> Dict[str, Any]:
        """Obtain a key-value map representing the configuration settings.

        The keys use the "." delimiter to denote going down a level in the configuration hierarchy.

        Returns:
            Dict[str, Any]: the map
        """
        params = dict()
        for k, v in self.items():
            if isinstance(v, CfgNode):
                for child_k, child_v in v.params_dict().items():
                    params[k + "." + child_k] = child_v
            else:
                params[k] = v
        return params
