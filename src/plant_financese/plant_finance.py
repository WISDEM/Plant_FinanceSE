from openmdao.api import Component
import numpy as np

class PlantFinance(Component):
    def __init__(self, verbosity = False):
        super(PlantFinance, self).__init__()

        # Inputs
        self.add_param('turbine_cost' ,     val=0.0, units='USD',   desc='A wind turbine capital cost')
        self.add_param('turbine_number',    val=0,                  desc='Number of turbines at plant', pass_by_obj=True)
        self.add_param('turbine_bos_costs', val=0.0, units='USD',   desc='Balance of system costs of the turbine')
        self.add_param('turbine_avg_annual_opex',val=0.0, units='USD',desc='Average annual operational expenditures of the turbine')
        self.add_param('park_aep',          val=0.0, units='kW*h',  desc='Annual Energy Production of the wind plant')
        self.add_param('turbine_aep',       val=0.0, units='kW*h',  desc='Annual Energy Production of the wind turbine')
        self.add_param('wake_loss_factor',  val=0.0,                desc='The losses in AEP due to waked conditions')
        self.add_param('machine_rating',  val=0.0, units='MW',                desc='rating of the turbine')

        # parameters
        self.add_param('fixed_charge_rate', val=0.12,               desc = 'Fixed charge rate for coe calculation')
        #self.add_param('sea_depth',         val=0.0, units='m',    desc = 'Sea depth of project for offshore, (0 for onshore)')

        #Outputs
        self.add_output('lcoe',             val=0.0, units='USD/kW',desc='Levelized cost of energy for the wind plant')
        
        self.verbosity = verbosity
        
    
    def solve_nonlinear(self, params, unknowns, resids):
        # Unpack parameters
        #depth       = params['sea_depth']
        n_turbine   = params['turbine_number']
        c_turbine   = params['turbine_cost'] 
        c_bos_turbine  = params['turbine_bos_costs'] 
        c_opex_turbine = params['turbine_avg_annual_opex'] 
        fcr         = params['fixed_charge_rate']
        wlf         = params['wake_loss_factor']
        turb_aep    = params['turbine_aep']
        t_rating    = params['machine_rating']
        
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
                park_aep     =  n_turbine * turb_aep * (1. - wlf)
                dpark_dtaep  =  n_turbine            * (1. - wlf)
                dpark_dnturb =              turb_aep * (1. - wlf)
                dpark_dwlf   = -n_turbine * turb_aep
                dpark_dpaep  = 0.0
            else:
                exit('ERROR: AEP is not connected properly. Both turbine_aep and park_aep are currently equal to 0 Wh. Check the connections to Plant_FinanceSE')
        else:
            park_aep    = params['park_aep']
            dpark_dpaep = 1.0
            dpark_dtaep = dpark_dnturb = dpark_dwlf = 0.0
        
        npr           = n_turbine * t_rating # net park rating, used in net energy capture calculation below
        dnpr_dnturb   =             t_rating
        dnpr_dtrating = n_turbine
        
        nec           = park_aep     / (npr * 1.e003) # net energy rating, per COE report
        dnec_dwlf     = dpark_dwlf   / (npr * 1.e003)
        dnec_dtaep    = dpark_dtaep  / (npr * 1.e003)
        dnec_dpaep    = dpark_dpaep  / (npr * 1.e003)
        dnec_dnturb   = dpark_dnturb / (npr * 1.e003) - dnpr_dnturb   * nec / npr
        dnec_dtrating =                               - dnpr_dtrating * nec / npr
        
        icc     = (c_turbine + c_bos_turbine) / (t_rating * 1.e003) #$/kW, changed per COE report
        c_opex  = (c_opex_turbine) / (t_rating * 1.e003)  # $/kW, changed per COE report

        dicc_dtrating   = -icc / t_rating
        dcopex_dtrating = -c_opex / t_rating
        dicc_dcturb = dicc_dcbos = dcopex_dcopex = 1.0 / (t_rating * 1.e003)

        '''
        GB 7 Aug 2019: Need to double check this one
        if offshore:
           # warranty Premium 
           icc += (c_turbine * n_turbine / 1.10) * 0.15
           dicc_dcturb += (n_turbine / 1.10) * 0.15
           dicc_dnturb = (c_turbine / 1.10) * 0.15
        '''
           
        #compute COE and LCOE values
        lcoe = ((icc * fcr + c_opex) / nec) # changed per COE report
        unknowns['lcoe'] = lcoe
        
        self.J = {}
        self.J['lcoe', 'turbine_cost'            ] = dicc_dcturb*fcr /nec
        self.J['lcoe', 'turbine_number'          ] = dicc_dnturb*fcr /nec - dnec_dnturb*lcoe/nec
        self.J['lcoe', 'turbine_bos_costs'       ] = dicc_dcbos *fcr /nec
        self.J['lcoe', 'turbine_avg_annual_opex' ] = dcopex_dcopex   /nec
        self.J['lcoe', 'fixed_charge_rate'       ] = icc / nec
        self.J['lcoe', 'wake_loss_factor'        ] = -dnec_dwlf *lcoe/nec
        self.J['lcoe', 'turbine_aep'             ] = -dnec_dtaep*lcoe/nec
        self.J['lcoe', 'park_aep'                ] = -dnec_dpaep*lcoe/nec
        self.J['lcoe', 'machine_rating'          ] = (dicc_dtrating*fcr + dcopex_dtrating)/nec - dnec_dtrating*lcoe/nec
        
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
            print('Wake loss factor                 %.2f %%'         % (wlf * 100.))         
            print('AEP of the single turbine        %.3f GWh'        % (turb_aep * 1.e-006))    
            print('AEP of the wind plant            %.3f GWh'        % (park_aep * 1.e-006))   
            print('Capital costs                    %.2f $/kW'       % icc) #added
            print('NEC                              %.2f MWh/MW/yr'  % nec) #added
            print('Outputs:')
            print('LCoE                             %.3f USD/MW'     % (unknowns['lcoe']  * 1.e003)) #removed "coe", best to have only one metric for cost
            print('################################################')
            
                    

    def linearize(self, params, unknowns, resids):
        
        return self.J

