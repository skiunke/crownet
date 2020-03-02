import re
from string import Template
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from oppanalyzer import utils


class OppFilterItem:
    """
    Filter item applicable to OMNeT++ based data frame. #name corresponds to column of df.
    """

    def __init__(self, name, value, regex):
        self.name = name
        self.value = value
        self.regex = regex

    def __str__(self):
        return self.value

    def __repr__(self) -> str:
        return (
            f"FilterItem(name: {self.name}, value: {self.value}, regex: {self.regex})"
        )


class OppTex:
    def __init__(self, opp=None):
        self._opp = opp

    @staticmethod
    def esc_tex(val: str):
        val = val.replace("&", "\&")
        val = val.replace("%", "\%")
        val = val.replace("$", "\$")
        val = val.replace("#", "\#")
        val = val.replace("_", "\_")
        val = val.replace("{", "\{")
        val = val.replace("}", "\}")
        val = val.replace("~", "\~")
        val = val.replace("^", "\^")
        val = val.replace("\\", "\\")

        return val

    @classmethod
    def write_module_summary(cls, run_id, module_dict: dict):

        module_list = []
        tex_mod_item = utils.tex_module_item_tmpl
        for _, v in module_dict.items():
            module_list.append(
                Template(tex_mod_item,).substitute(
                    module=cls.esc_tex(str(v["module"])),
                    scalar=cls.esc_tex(str(v["scalar"])),
                    vector=cls.esc_tex(str(v["vector"])),
                    histogram=cls.esc_tex(str(v["histogram"])),
                )
            )

        tex_mod = utils.tex_module_tmpl
        return Template(tex_mod).substitute(
            run=cls.esc_tex(run_id), module_items="".join(module_list)
        )

    @classmethod
    def write_attribute_tabular(cls, run_id, runattr_dict, itervars_dict, param_dict):
        tex_tmpl = utils.tex_tabluar_tmpl

        runattrs = "   \\\\ \n".join(
            [
                f"\t\t{cls.esc_tex(k)} & {cls.esc_tex(str(v))}"
                for (k, v) in runattr_dict.items()
            ]
        )

        itervars = "   \\\\ \n".join(
            [
                f"\t\t{cls.esc_tex(k)} & {cls.esc_tex(str(v))}"
                for (k, v) in itervars_dict.items()
            ]
        )

        params = "   \\\\ \n".join(
            [
                f"\t\t{cls.esc_tex(k)} & {cls.esc_tex(str(v))}"
                for (k, v) in param_dict.items()
            ]
        )

        return Template(tex_tmpl).substitute(
            runattrs=runattrs,
            itervars=itervars,
            params=params,
            run=cls.esc_tex(run_id),
        )

    def create_module_summary(self, run_id, output_file=None):
        """
        Create latex table for module summary.
        :param run_id:      run_id for which tex is created
        :param output_file: if not set use to stdout
        """

        modType = np.array(self._opp._obj[["module", "type"]])
        module_dict = {}
        for m in modType:
            data = module_dict.get(
                m[0], {"module": m[0], "scalar": 0, "vector": 0, "histogram": 0}
            )
            data[m[1]] = data.get(m[1], 0) + 1
            module_dict.setdefault(m[0], data)

        tmpl = self.write_module_summary(run_id=run_id, module_dict=module_dict)

        if output_file is None:
            print(tmpl)
        else:
            with open(output_file, "w") as f:
                f.write(tmpl)

    def create_attribute_tabular(self, run_id, output_file=None):
        """
        Create latex table for attribute data.
        :param run_id:      run_id for which tex is created
        :param output_file: if not set use to stdout
        """

        tmpl = self.write_attribute_tabular(
            run_id=run_id,
            runattr_dict=self._opp.attr[run_id]["runattr"],
            itervars_dict=self._opp.attr[run_id]["itervar"],
            param_dict=self._opp.attr[run_id]["param"],
        )

        if output_file is None:
            print(tmpl)
        else:
            with open(output_file, "w") as f:
                f.write(tmpl)


class OppFilter:
    """
    Builder pattern for OMNeT based data frames. This allows simplified selection of
    rows of the dataframe. Most columns of the data frame has two methods.
    <column_name> and <column_name>_regex. The former accepts only perfect matches
    whereas the later accepts a regex matter. If allow_number_range=True of the
    regex method is True number ranges such as '.*foo\[3..5\]\.bar\.baz' will be accepted
    and replaced with '.*foo\[\[3|4|5]]\.bar\.baz'.
    Note: All special characters must be escaped if literal brackets or dots should be matched.
    """

    def __init__(self, df: pd.DataFrame = None, data_only=True):
        self._filter_dict = {}
        self._name = None
        self._name_regex = None
        self._run = None
        self._run_regex = None
        self._type = None
        self._module = None
        self._module_regex = None
        self._data_only = data_only
        self._number_range_pattern = re.compile(
            "(?P<n_range>(?P<start>\d+)\.\.(?P<end>\d+))"
        )
        self._df = df
        if data_only:
            self._add_filter(
                OppFilterItem("type", "(scalar|vector|histogram)", regex=True)
            )

    def _apply_number_range(self, val):
        matches = re.findall(self._number_range_pattern, val)
        for match in matches:
            old_range = match[0]
            start = int(match[1])
            end = int(match[2])
            if start < end:
                range_new = (
                    "[" + "|".join([str(i) for i in range(start, end + 1)]) + "]"
                )
                val = val.replace(old_range, range_new)
            else:
                raise ValueError(f"number range in regex {val} invalid")
        return val

    def _add_filter(self, f: OppFilterItem):
        self._filter_dict[f.name] = f

    def name(self, name):
        self._add_filter(OppFilterItem("name", name, False))
        return self

    def name_regex(self, name: str, allow_number_range=True):
        if allow_number_range:
            name = self._apply_number_range(name)

        self._add_filter(OppFilterItem("name", name, True))
        return self

    def run(self, run):
        self._add_filter(OppFilterItem("run", run, False))
        return self

    def run_regex(self, run: str, allow_number_range=True):
        if allow_number_range:
            run = self._apply_number_range(run)

        self._add_filter(OppFilterItem("run", run, True))
        return self

    def module(self, module):
        self._add_filter(OppFilterItem("module", module, False))
        return self

    def module_regex(self, module: str, allow_number_range=True):
        if allow_number_range:
            module = self._apply_number_range(module)

        self._add_filter(OppFilterItem("module", module, True))
        return self

    def scalar(self):
        self._add_filter(OppFilterItem("type", "scalar", False))
        return self

    def vector(self):
        self._add_filter(OppFilterItem("type", "vector", False))
        return self

    def apply(self, df: pd.DataFrame = None):

        if df is not None:
            self._df = df

        if self._df is None:
            raise ValueError("no Dataframe set")

        bool_filter = pd.Series(
            [True for _ in range(0, self._df.shape[0])], self._df.index
        )
        for key, filter_item in self._filter_dict.items():
            if filter_item.regex:
                bool_filter = bool_filter & self._df.loc[:, key].str.match(
                    filter_item.value
                )
            else:
                bool_filter = bool_filter & (self._df.loc[:, key] == filter_item.value)
        return self._df.loc[bool_filter]

    def __str__(self) -> str:
        return self._filter_dict.__str__()

    def __repr__(self) -> str:
        ret = "Filter: "
        for key, value in self._filter_dict.items():
            ret += f"\n   {value.__repr__()}"
        return ret


class OppAttributes:
    """
    Helper to access Attributes from OMNeT++ DataFrame
    """

    def __init__(self, df):
        self._df = df

    def run_parameter(self, run):
        ret = self._df.loc[
            (self._df["run"] == run) & (self._df["type"] == "param"),
            ("attrname", "attrvalue"),
        ]
        if ret.shape[0] == 0:
            raise ValueError(f"no data for run={run}")
        return ret

    def run_parameter_dict(self, run):
        ret = self.run_parameter(run)
        return {r[1][0]: r[1][1] for r in ret.iterrows()}

    def run_attr(self, run):
        ret = self._df.loc[
            (self._df["run"] == run) & (self._df["type"] == "runattr"),
            ("attrname", "attrvalue"),
        ]
        if ret.shape[0] == 0:
            raise ValueError(f"no data for run={run}")
        return ret

    def run_attr_dict(self, run):
        ret = self.run_attr(run)
        return {r[1][0]: r[1][1] for r in ret.iterrows()}

    def statistics_meta_data(self, run, module, stat_name):
        r = {
            "run": run,
            "module": module,
            "name": stat_name,
            "title": "???",
            "unit": "???",
        }
        ret = self._df.loc[
            (self._df["run"] == run)
            & (self._df["type"] == "attr")
            & (self._df["module"] == module)
            & (self._df["name"] == stat_name),
            ("attrname", "attrvalue"),
        ]
        if ret.shape[0] == 0:
            raise ValueError(
                f"no meta data for run={run}, module={module}, name={stat_name}"
            )
        r.update({r[1][0]: r[1][1] for r in ret.iterrows()})
        return r

    def attr_for_series(self, s: pd.Series):
        return self.statistics_meta_data(run=s.run, module=s.module, stat_name=s.name)


class OppPlot:
    """
    Plot helper functions.

    set_xlabel
    set_xlimit(left, right)
    set_xscale() [linear, log, symlog, logit]
    set_xlimit
    set_xmargin

    set_xticks
    set_xticklabels

    """

    default_plot_args = {"linewidth": 0, "markersize": 3, "marker": ".", "color": "b"}

    plot_marker = [".", "*", "o", "v", "1", "2", "3", "4"]
    plot_color = ["b", "g", "r", "c", "m", "y", "k", "w"]

    @classmethod
    def marker(cls, idx):
        return cls.plot_marker[idx % len(cls.plot_marker)]

    @classmethod
    def color(cls, idx):
        return cls.plot_color[idx % len(cls.plot_color)]

    @classmethod
    def plt_args(cls, idx=0, *args, **kwargs):
        ret = dict(cls.default_plot_args)
        if "label" not in kwargs.keys():
            ret.setdefault("label", f"{idx}-data")

        ret.update(
            {"marker": cls.marker(idx), "color": cls.color(idx),}
        )
        if kwargs:
            ret.update(kwargs)
        return ret

    @classmethod
    def create_label(cls, lbl_str: str, remove_filter: List[str] = None):

        if remove_filter is not None:
            for rpl in remove_filter:
                lbl_str = lbl_str.replace(rpl, "")

        return lbl_str

    def __init__(self, accessor):
        self._opp = accessor

    def _set_labels(self, ax: plt.axes, s: pd.Series, xlabel="time [s]"):
        ax.set_xlabel(xlabel)
        attr = self._opp.attr_for_series(s)
        ax.set_ylabel(f"[{attr['unit']}]")
        ax.set_title(attr["title"])

    def create_time_series(self, ax: plt.axes, s: pd.Series, *args, **kwargs):
        self._set_labels(ax, s)
        if "label" not in kwargs:
            kwargs.setdefault("label", self.create_label(s.module, []))
        ax.plot(s.vectime, s.vecvalue, **self.plt_args(idx=0, **kwargs))

    def create_histogram(self, ax: plt.axes, s: pd.Series, bins=40):
        ax.hist(
            s.vecvalue, bins, density=True,
        )
        attr = self._opp.attr_for_series(s)
        ax.set_title(attr["title"])
        ax.set_xlabel(f"[{attr['unit']}]")


@pd.api.extensions.register_dataframe_accessor("opp")
class OppAccessor:
    """
    see https://pandas.pydata.org/pandas-docs/stable/development/extending.html
    opp namespace to access attribute information for scalar, vector and
    histogram types, helpers to access data via filters and helpers to create
    simple plots like time series and histogram plots.

    See classes #OppAttributes, #OppFilter, OppFilterItem and #OppPlot for more detail.
    """

    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj: pd.DataFrame = pandas_obj
        self.plot: OppPlot = OppPlot(self)
        self.tex: OppTex = OppTex(self)
        self.attr: OppAttributes = OppAttributes(self)

    # @property
    # def plot(self):
    #     if self._plot is None:
    #         raise ValueError(
    #             "OppAccessor not fully initialized. Did you call opp.pre_process()?"
    #         )
    #     return self._plot
    #
    # @property
    # def tex(self):
    #     if self._tex is None:
    #         raise ValueError(
    #             "OppAccessor not fully initialized. Did you call opp.pre_process()?"
    #         )
    #     return self._tex

    #
    # def pre_process(self):
    #     """
    #     :return: returns copy!
    #     """
    #     # subset of attribute information
    #     run_cnf = self._obj.loc[
    #         (self._obj.type == "runattr")
    #         | (self._obj.type == "param")
    #         | (self._obj.type == "itervar"),
    #         ["run", "type", "attrname", "attrvalue"],
    #     ]
    #
    #     self._obj.drop(self._obj.loc[(self._obj.type == "runattr")].index, inplace=True)
    #     self._obj.drop(self._obj.loc[(self._obj.type == "param")].index, inplace=True)
    #     self._obj.drop(self._obj.loc[(self._obj.type == "itervar")].index, inplace=True)
    #
    #     attr = self._obj.loc[
    #         self._obj.type == "attr", ["run", "module", "name", "attrname", "attrvalue"]
    #     ]
    #     attr["full_data_path"] = attr.module + "." + attr.name
    #
    #     # drop rows with attribute information
    #     self._obj.drop(self._obj.loc[self._obj.type == "attr"].index, inplace=True)
    #
    #     # add run_id column
    #     self._obj["run_id"] = self._obj["run"].copy()
    #     runs = self._obj["run_id"].unique()
    #     runs.sort()
    #     self._obj["run_id"] = self._obj["run_id"].apply(
    #         lambda x: np.where(runs == x)[0][0]
    #     )
    #
    #     _opp_attr_dict = {}
    #     for _, row in run_cnf.iterrows():
    #         # get dictionary for run or create new one
    #         run_dict = _opp_attr_dict.get(row["run"], {})
    #
    #         # write item
    #         item = run_dict.get(row["type"], {})
    #         item.setdefault(row["attrname"], row["attrvalue"])
    #
    #         # write back
    #         run_dict.setdefault(row["type"], item)
    #         _opp_attr_dict.setdefault(row["run"], run_dict)
    #
    #     for _, row in attr.iterrows():
    #         # get dictionary for run or create new one
    #         run_dict = _opp_attr_dict.get(row["run"], {})
    #
    #         # write item
    #         item = run_dict.get(row["full_data_path"], {})
    #         item.setdefault(row["attrname"], row["attrvalue"])
    #         item.setdefault("module", row["module"])
    #         item.setdefault("name", row["name"])
    #
    #         # write back
    #         run_dict.setdefault(row["full_data_path"], item)
    #         _opp_attr_dict.setdefault(row["run"], run_dict)
    #
    #     # run->runattr->{all run attributes for run}
    #     # run->full_data_path->{all attributes for full_module_path in run}
    #     # full_data_path is the combination of "<module>.<name>" columns were name is the name of the data point.
    #     self.attr: OppAttributes = OppAttributes(_opp_attr_dict, self._obj)
    #     print("OppAccessor initialized")
    #     return self._obj.copy()

    @staticmethod
    def _validate(obj: pd.DataFrame):
        cols = ["run", "type", "module", "name", "attrname", "attrvalue"]
        for c in cols:
            if c not in obj.columns:
                raise AttributeError(f"Must have '{c}' column. ")

    def module_summary(self):
        ret = self._obj[
            self._obj.type.isin(["scalar", "histogram", "vector"])
        ].module.unique()
        ret.sort()
        return ret

    def name_summary(self):
        ret = self._obj[
            self._obj.type.isin(["scalar", "histogram", "vector"])
        ].name.unique()
        ret.sort()
        return ret

    def filter(self, f: OppFilter = None, data_only=True):
        if f is not None:
            return f.apply(self._obj)
        else:
            return OppFilter(self._obj, data_only)
