from openmdao.api import Component
import numpy as np

class PlantFinance(Component):
    def __init__(self, verbosity = False):
        super(PlantFinance, self).__init__()

        self.amortFactor = None
        
        # Inputs
        self.add_param('turbine_cost' ,     val=0.0, units='USD',   desc='A wind turbine capital cost')
        self.add_param('turbine_number',    val=0,                  desc='Number of turbines at plant', pass_by_obj=True)
        self.add_param('turbine_bos_costs', val=0.0, units='USD',   desc='Balance of system costs of the turbine')
        self.add_param('turbine_avg_annual_opex',val=0.0, units='USD',desc='Average annual operational expenditures of the turbine')
        self.add_param('park_aep',          val=0.0, units='kW*h',  desc='Annual Energy Production of the wind plant')
        self.add_param('turbine_aep',       val=0.0, units='kW*h',  desc='Annual Energy Production of the wind turbine')
        self.add_param('wake_loss_factor',  val=0.0,                desc='The losses in AEP due to waked conditions')
        self.add_param('net_energy_capture',  val=0.0, units='MWh/MW/yr',                desc='total energy of the plant')
        self.add_param('machine_rating',  val=0.0, units='MW',                desc='rating of the turbine')

        # parameters
        self.add_param('fixed_charge_rate', val=0.12,               desc = 'Fixed charge rate for coe calculation')
        self.add_param('tax_rate',          val=0.4,                desc = 'Tax rate applied to operations')
        self.add_param('discount_rate',     val=0.07,               desc = 'Applicable project discount rate')
        self.add_param('construction_time', val=1.0,  units='year', desc = 'Number of years to complete project construction')
        self.add_param('project_lifetime',  val=20.0, units='year', desc = 'Project lifetime for LCOE calculation')
        self.add_param('sea_depth',         val=0.0, units='m',    desc = 'Sea depth of project for offshore, (0 for onshore)')

        #Outputs
        self.add_output('lcoe',             val=0.0, units='USD/kW',desc='Levelized cost of energy for the wind plant')
        self.add_output('coe',              val=0.0, units='USD/kW',desc='Cost of energy for the wind plant - unlevelized')

        
        self.verbosity = verbosity
        
    
    def solve_nonlinear(self, params, unknowns, resids):
        # Unpack parameters
        depth       = params['sea_depth']
        n_turbine   = params['turbine_number']
        c_turbine   = params['turbine_cost'] 
        c_bos_turbine  = params['turbine_bos_costs'] 
        c_opex_turbine = params['turbine_avg_annual_opex'] 
        fcr         = params['fixed_charge_rate']
        tax         = params['tax_rate']
        r           = params['discount_rate']
        wlf         = params['wake_loss_factor']
        turb_aep    = params['turbine_aep']
        park_aep    = params['park_aep']
        t_construct = params['construction_time']
        t_project   = params['project_lifetime']
        t_rating    = params['machine_rating']
        npr         = params['turbine_number'] * params['machine_rating'] # net park rating, used in net energy capture calculation below
        nec         = params['turbine_aep'] * params['turbine_number'] / (npr * 1.e003) # net energy rating, per COE report
        
        # Handy offshore boolean flag
        offshore = (depth > 0.0)
        
        # Run a few checks on the inputs
        if n_turbine == 0:
            exit('ERROR: The number of the turbines in the plant is not initialized correctly and it is currently equal to 0. Check the connections to Plant_FinanceSE')
        
        if c_turbine == 0:
            exit('ERROR: The cost of the turbines in the plant is not initialized correctly and it is currently equal to 0 USD. Check the connections to Plant_FinanceSE')
            
        if c_bos_turbine == 0:
            print('WARNING: The BoS costs of the turbine are not initialized correctly and they are currently equal to 0 USD. Check the connections to Plant_FinanceSE')
        
        if c_opex_turbine == 0:
            print('WARNING: The Opex costs of the turbine are not initialized correctly and they are currently equal to 0 USD. Check the connections to Plant_FinanceSE')
        
        if park_aep == 0:
            if turb_aep != 0:
                park_aep = n_turbine * turb_aep * (1. - wlf)
            else:
                exit('ERROR: AEP is not connected properly. Both turbine_aep and park_aep are currently equal to 0 Wh. Check the connections to Plant_FinanceSE')
        
        
        icc     = (c_turbine + c_bos_turbine) / (t_rating * 1.e003) #$/kW, changed per COE report
        c_opex  = (c_opex_turbine) / (t_rating * 1.e003)  # $/kW, changed per COE report

        
        if offshore:
           # warranty Premium 
           icc += (c_turbine * n_turbine / 1.10) * 0.15
        
        #compute COE and LCOE values
        unknowns['lcoe'] = ((icc * fcr + c_opex) / nec) # changed per COE report

        if self.verbosity == True:
            print('################################################')
            print('Computation of CoE and LCoE from Plant_FinanceSE')
            print('Inputs:')
            print('Water depth                      %.2f m'          % depth)
            print('Number of turbines in the park   %u'              % n_turbine)
            print('Cost of the single turbine       %.3f M USD'      % (c_turbine * 1.e-006))  
            print('BoS costs of the single turbine  %.3f M USD'      % (c_bos_turbine * 1.e-006))  
            print('Initial capital cost of the park %.3f M USD'      % (icc * 1.e-006))  
            print('Opex costs of the single turbine %.3f M USD'      % (c_opex_turbine * 1.e-006))
            print('Opex costs of the park           %.3f M USD'      % (c_opex * 1.e-006))              
            print('Fixed charge rate                %.2f %%'         % (fcr * 100.))     
            print('Tax rate                         %.2f %%'         % (tax * 100.))        
            print('Discount rate                    %.2f %%'         % (r * 100.))        
            print('Wake loss factor                 %.2f %%'         % (wlf * 100.))         
            print('AEP of the single turbine        %.3f GWh'        % (turb_aep * 1.e-006))    
            print('AEP of the wind plant            %.3f GWh'        % (park_aep * 1.e-006))   
            print('Construction time                %.2f yr'         % t_construct)
            print('Project lifetime                 %.2f yr'         % t_project)
            print('Capital costs                    %.2f $/kW'       % icc) #added
            print('NEC                              %.2f MWh/MW/yr'  % nec) #added
            print('Outputs:')
            print('LCoE                             %.3f USD/MW'     % (unknowns['lcoe']  * 1.e003)) #removed "coe", best to have only one metric for cost
            print('################################################')
            
                    

    def linearize(self, params, unknowns, resids):
        # Unpack parameters
        depth       = params['sea_depth']
        n_turbine   = params['turbine_number']
        fcr         = params['fixed_charge_rate']
        tax         = params['tax_rate']
        r           = params['discount_rate']
        wlf         = params['wake_loss_factor']
        turb_aep    = params['turbine_aep']
        park_aep    = params['park_aep']
        t_construct = params['construction_time']
        t_project   = params['project_lifetime']

        # Handy offshore boolean flag
        offshore = (depth > 0.0)
        
        # Run a few checks on the inputs
        if n_turbine == 0:
            exit('ERROR: The number of the turbines in the plant is not initialized correctly and it is currently equal to 0. Check the connections to Plant_FinanceSE')
        
        if park_aep == 0:
            if turb_aep != 0:
                park_aep = n_turbine * turb_aep * (1. - wlf)
            else:
                exit('ERROR: AEP is not connected properly. Both turbine_aep and park_aep are currently equal to 0 Wh. Check the connections to Plant_FinanceSE')
        
        
        dicc_dcturb = n_turbine
        dicc_dcbos  = 1.0
        if offshore:
            dicc_dcturb = n_turbine * (1.0 + 0.15 / 1.10)
            
        dcoe_dcturb = dicc_dcturb * fcr / park_aep
        dcoe_dcbos  = dicc_dcbos  * fcr / park_aep
        dcoe_dopex  = (1. - tax)        / park_aep
        dcoe_daep   = -unknowns['coe']  / park_aep

        dlcoe_dcturb = dicc_dcturb * self.amortFactor / park_aep
        dlcoe_dcbos  = dicc_dcbos  * self.amortFactor / park_aep
        dlcoe_dopex  = 1.0                            / park_aep
        dlcoe_daep   = -unknowns['lcoe']              / park_aep

        J = {}
        J['coe' , 'turbine_cost'   ] = dcoe_dcturb
        J['coe' , 'bos_cost'       ] = dcoe_dcbos
        J['coe' , 'avg_annual_opex'] = dcoe_dopex
        J['coe' , 'net_aep'        ] = dcoe_daep
        J['lcoe', 'turbine_cost'   ] = dlcoe_dcturb
        J['lcoe', 'bos_cost'       ] = dlcoe_dcbos
        J['lcoe', 'avg_annual_opex'] = dlcoe_dopex
        J['lcoe', 'net_aep'        ] = dlcoe_daep
        
        return J

