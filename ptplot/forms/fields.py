from django import forms
from ptplot.science.mission_profile import MISSION_PROFILE_CHOICES


class MissionProfileField(forms.TypedChoiceField):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            label=r"Mission profile",
            choices=MISSION_PROFILE_CHOICES,
            coerce=int,
            empty_value=None,
            **kwargs
        )

    # def to_python(self, value) -> tp.Optional[MissionProfile]:
    #     if value is None or value == "":
    #         return None
    #     converted = int(super().to_python(value))
    #     return MissionProfile.from_ind(converted)
