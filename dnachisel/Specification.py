import copy
import re

from .SequencePattern import DnaNotationPattern, enzyme_pattern
from .biotools import find_specification_in_feature
from .Location import Location
from .SpecEvaluation import SpecEvaluation
from Bio.SeqFeature import SeqFeature

class Specification:
    """General class to define specifications to optimize.

    Note that all specifications have a ``boost`` attribute that is a
    multiplicator that will be used when computing the global specification
    score of a problem with ``problem.all_objectives_score()``.

    New types of specifications are defined by subclassing ``Specification`` and
    providing a custom ``evaluate`` and ``localized`` methods.

    Parameters
    -----------
    evaluate
      function (sequence) => SpecEvaluation
    boost
      Relative importance of the Specification's score in a multi-specification
      problem.
    """

    best_possible_score = None
    optimize_passively = False
    enforced_by_nucleotide_restrictions = False
    priority = 0

    def __init__(self, evaluate=None, boost=1.0):
        """Initialize."""
        self.boost = boost
        if evaluate is not None:
            self.evaluate = evaluate

    def localized(self, location):
        """Return a modified version of the specification for the case where
        sequence modifications are only performed inside the provided location.

        For instance if an specification concerns local GC content, and we are
        only making local mutations to destroy a restriction site, then we only
        need to check the local GC content around the restriction site after
        each mutation (and not compute it for the whole sequence), so
        ``EnforceGCContent.localized(location)`` will return an specification
        that only looks for GC content around the provided location.

        If an specification concerns a DNA segment that is completely disjoint
        from the provided location, this must return a ``VoidSpecification``.

        Must return an object of class ``Constraint``.
        """
        return self

    def copy_with_changes(self, **kwargs):
        """Return a copy of the Specification with modified properties.

        For instance ``new_spec = spec.copy_with_changes(boost=10)``.
        """
        new_specification = copy.deepcopy(self)
        new_specification.__dict__.update(kwargs)
        return new_specification

    def initialize_on_problem(self, problem, role="constraint"):
        """Complete specification initialization when the sequence gets known.

        Some specifications like to know what their role is and on which
        sequence they are employed before they complete some values.
        """
        return self

    @staticmethod
    def from_biopython_feature(feature, specifications_dict):
        """Parse a Biopython feature create an annotation.

        The specifications_dict enables to map specification names to the
        actual implemented class.

        """
        def format_value(value):
            match = re.match(r"'(.*)'", value)
            if match is not None:
                return match.groups()[0]
            else:
                try:
                    return int(value)
                except ValueError:
                    try:
                        return float(value)
                    except:
                        return value

        label = find_specification_in_feature(feature)
        if isinstance(label, list):
            label = label[0]
        if not label.endswith(")"):
            label += "()"
        pattern = "([@~])(\S+)(\(.*\))"
        match = re.match(pattern, label)
        role, specification, parameters = match.groups()
        role = {"@": "constraint", "~": "objective"}[role]
        args, kwargs = [], {}
        for arg in parameters[1:-1].split(', '):
            if "=" in arg:
                key, value = arg.split('=')
                kwargs[key] = format_value(value)
            else:
                args.append(format_value(arg))

        kwargs["location"] = Location.from_biopython_location(feature.location)
        return role, specifications_dict[specification](*args, **kwargs)

    def label(self, role=None, with_location=True):
        prefix = {'constraint': '@', 'objective': '~', None: ''}[role]
        if with_location and hasattr(self, 'location') and self.location:
            location = '[%s]' % self.location
        else:
            location = ''
        params = self.label_parameters()
        if params == []:
            params = ""
        else:
            params = "(%s)" % ", ".join([
                "=".join(p) if isinstance(p, tuple) else p
                for p in params
            ])
        return "".join([prefix, self.__class__.__name__, location, params])

    def label_parameters(self):
        return []

    def __str__(self):
        return self.label()

    def __repr__(self):
        return self.label()


    def to_biopython_feature(self, feature_type="misc_feature",
                             role="constraint", colors_dict=None,
                             **qualifiers):
        """Return a Biopython feature representing the specification.

        The feature label is a string representation of the specification,
        and its location indicates the specification's scope.

        """
        if colors_dict is None:
            colors_dict = {"constraint": "#355c87", "objective": "#f9cd60"}
        qualifiers["role"] = role
        if "label" not in qualifiers:
            qualifiers['label'] = self.label(role=role, with_location=False)

        if "color" not in qualifiers:
            qualifiers['color'] = colors_dict[role]
        return SeqFeature(self.location.to_biopython_location(),
                          type=feature_type,
                          qualifiers=qualifiers)

    def restrict_nucleotides(self, sequence, location=None):
        """Restrict the possible nucleotides mutations in a sequence to speed
        up optimization.

        This method has no effect unless a special heuristic is implemented
        for it.
        """
        return []

    def as_passive_objective(self):
        return self.copy_with_changes(optimize_passively=True)
