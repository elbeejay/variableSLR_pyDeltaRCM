"""Custom model to handle variable SLR scenarios."""
import pyDeltaRCM


class VariableSLRModel(pyDeltaRCM.DeltaModel):
    """Subclass of pyDeltaRCM.DeltaModel with customized behavior."""
    def __init__(self, input_file=None, **kwargs):

        # inherit base DeltaModel methods
        super().__init__(input_file, **kwargs)

    def hook_import_files(self):
        """Define custom YAML parameters."""
        # SLR in mm
        self.subclass_parameters['SLR_mm'] = {
            'type': ['int', 'float'], 'default': 0
        }
        # SLR variation type
        self.subclass_parameters['SLR_type'] = {
            'type': 'str', 'default': 'steady'
        }

    def hook_init_output_file(self):
        """Save the SLR in mm/yr."""
        # SLR in mm/yr
        self._save_var_list['meta']['SLR_mm'] = [
            'SLR_mm', 'mm per year', 'f4', ()]

    def hook_create_other_variables(self):
        """Use hook to set SLR value based on SLR_mm.

        At this point model attributes have been set, so can use them
        to re-set the SLR one. Will try to write to log at this time
        as well to reflect updated value."""
        # assumes 10 bankfull discharge days per year
        self.SLR = self.SLR_mm / 1000 / 10 / 24 / 60 / 60
        # log updated SLR rate
        _msg = 'Re-configured final SLR based on mm/yr and style: ' + \
            str(self.SLR)
        self.log_info(_msg, verbosity=0)
        # define gradual increase rate for SLR if needed
        if self.SLR_type == 'gradual':
            self.SLR_delta = self.SLR / 12100  # note: hardcoded to 12100 timesteps
            self.SLR = 0.0  # initial SLR is 0.0
        # define final SLR in abrupt case
        if self.SLR_type == 'abrupt':
            self.SLR_final = self.SLR
            self.SLR = 0.0  # initial SLR for first half is 0

    def hook_finalize_timestep(self):
        """Place where we update SLR rate if/as necessary."""
        # gradual case is a continuous increase in SLR
        if self.SLR_type == 'gradual':
            self.SLR += self.SLR_delta
        elif self.SLR_type == 'abrupt':
            # note: hardcoded assuming 12100 total timesteps
            if self._time_iter >= 6050:
                self.SLR = self.SLR_final