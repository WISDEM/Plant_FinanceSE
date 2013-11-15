"""
lcoe_cst-bos-ecn_ssembly.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys, os, fileinput
import numpy as np

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree
from openmdao.main.datatypes.api import Int, Bool, Float, Array, Str, Enum, VarTree

from twister.components.global_config import WESEConfig, get_dict

from twister.components.varTrees import Turbine, PlantBOS, PlantOM

# Import key assemblies and components for TCC, BOS, O&M, Finance & AEP
from twister.assemblies.tcc_cst_assembly import tcc_cst_assembly
from twister.components.bos_nrel_offshore_component import bos_nrel_offshore_component
from twister.components.om_ecn_offshore_component  import om_ecn_offshore_component
from twister.components.fin_cst_component import fin_cst_component
from twister.assemblies.aep_weibull_assembly import aep_weibull_assembly

from twister.fused_cost import GenericFinancialAnalysis

# Drivetrain assembly specified at top level
from twister.models.csm.csmDriveEfficiency import DrivetrainEfficiencyModel, csmDriveEfficiency

class lcoe_cst_bos_ecn_assembly(Assembly):

    # ---- Design Variables ----------
    
    # Turbine configuration
    # drivetrain
    ratedPower = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    towerTopDiameter = Float(3.87, units= 'm', iotype='in', desc= 'tower top diameter in m')
    towerBottomDiameter = Float(6.0, units= 'm', iotype='in', desc= 'tower bottom diameter in m')
    towerTopThickness = Float(0.0247, units= 'm', iotype='in', desc= 'tower top thickness in m')
    towerBottomThickness = Float(0.0351, units= 'm', iotype='in', desc= 'tower bottom diameter in m')        
    
    # Plant configuration
    # climate
    shearExponent = Float(0.1, iotype='in', desc= 'shear exponent for wind plant') #TODO - could use wind model here
    windSpeed50m = Float(8.35, units = 'm/s', iotype='in', desc='mean annual wind speed at 50 m height')
    weibullK= Float(2.1, iotype='in', desc = 'weibull shape factor for annual wind speed distribution')
    altitude = Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
    airDensity = Float(0.0, units = 'kg / (m * m * m)', iotype='in', desc= 'air density at wind plant site')  # default air density value is 0.0 - forces aero csm to calculate air density in model
    seaDepth = Float(20.0, units = 'm', iotype='in', desc = 'sea depth for offshore wind project')
    distanceFromShore = Float(30.0, units = 'km', iotype='in', desc = 'distance of plant from shore')
    soilType = Str("Sand", iotype='in', desc = 'soil type at plant site')
    # plant operation
    soilingLosses = Float(0.0, iotype='in', desc = 'energy losses due to blade soiling for the wind plant - average across turbines')
    arrayLosses = Float(0.059, iotype='in', desc = 'energy losses due to turbine interactions - across entire plant')
    turbineNumber = Int(100, iotype='in', desc = 'total number of wind turbines at the plant')
    # financial
    year = Int(2009, units = 'yr', iotype='in', desc = 'year of project start')
    month = Int(12, units = 'mon', iotype='in', desc = 'month of project start')    
    fixedChargeRate = Float(0.12, iotype = 'in', desc = 'fixed charge rate for coe calculation')
    constructionFinancingRate = Float(0.03, iotype = 'in', desc = 'financing construction rate')
    taxRate = Float(0.4, iotype = 'in', desc = 'tax rate applied to operations')
    discountRate = Float(0.07, iotype = 'in', desc = 'applicable project discount rate')
    constructionTime = Float(1.0, iotype = 'in', desc = 'number of years to complete project construction')
    projectLifetime = Float(20.0, iotype = 'in', desc = 'project lifetime for LCOE calculation')

    # ------------- Outputs -------------- 
    # See passthrough variables below

    def __init__(self):
        """ Creates a new LCOE Assembly object """

        super(lcoe_cst_bos_ecn_assembly, self).__init__()

                
    def configure(self):
        ''' configures assembly by adding components, creating the workflow, and connecting the component i/o within the workflow '''

        super(lcoe_cst_bos_ecn_assembly, self).configure()

        ### temp fix since framework not working
        self.add('aep', aep_weibull_assembly())
        self.add('tcc', tcc_cst_assembly())
        self.add('bos', bos_nrel_offshore_component())
        self.add('opex',  om_ecn_offshore_component())
        self.add('fin', fin_cst_component()) 

        # connect inputs to component and assembly inputs
        self.driver.workflow.add(['tcc','bos','opex','aep','fin'])

        self.connect('tcc.turbine_cost','fin.turbine_cost')
        self.connect('bos.bos_cost','fin.bos_cost')
        self.connect('opex.avg_annual_opex','fin.avg_annual_opex')
        self.connect('aep.net_aep','fin.net_aep')

        self.create_passthrough('fin.lcoe')
        self.create_passthrough('aep.net_aep')
        #self.create_passthrough('aep.gross_aep')
        #self.create_passthrough('aep.capacity_factor')
        self.create_passthrough('opex.avg_annual_opex')
        self.create_passthrough('bos.bos_cost')
        self.create_passthrough('tcc.turbine_cost')
        ### end temp fix framework not working


        # turbine configuration
        # drivetrain
        self.connect('ratedPower', ['aep.ratedPower', 'tcc.ratedPower', 'bos.ratedPower', 'opex.ratedPower', 'fin.ratedPower'])
        self.connect('towerTopDiameter', ['tcc.towerTopD'])
        self.connect('towerBottomDiameter', ['tcc.towerBottomD'])
        self.connect('towerTopThickness', ['tcc.towerTopT'])
        self.connect('towerBottomThickness', ['tcc.towerBottomT'])

        # plant configuration
        # climate
        self.connect('shearExponent',['aep.shearExponent'])
        self.connect('windSpeed50m', ['aep.windSpeed50m'])
        self.connect('weibullK', ['aep.weibullK'])
        self.connect('seaDepth', ['tcc.seaDepth', 'bos.seaDepth'])
        self.connect('distanceFromShore', 'bos.distanceFromShore')
        self.connect('soilType', 'bos.soilType')
        # plant operation       
        self.connect('soilingLosses', ['aep.soilingLosses'])
        self.connect('arrayLosses', ['aep.arrayLosses'])
        self.connect('turbineNumber', ['aep.turbineNumber', 'bos.turbineNumber', 'opex.turbineNumber', 'fin.turbineNumber'])
 
        # financial
        self.connect('year', ['tcc.year'])
        self.connect('month', ['tcc.month'])
        self.connect('fixedChargeRate', 'fin.fixedChargeRate')
        self.connect('constructionFinancingRate', 'fin.constructionFinancingRate')
        self.connect('taxRate', 'fin.taxRate')
        self.connect('discountRate', 'fin.discountRate')
        self.connect('constructionTime', 'fin.constructionTime')
        self.connect('projectLifetime', ['fin.projectLifetime', 'opex.projectLifetime'])
               
        # connect i/o between components and assemblies
        self.connect('tcc.rotorDiameter', 'bos.rotorDiameter')
        self.connect('tcc.hubHeight', ['aep.hubHeight', 'bos.hubHeight'])
        self.connect('tcc.turbine_cost', ['opex.turbineCost'])
        self.connect('tcc.bladeLength','bos.bladeLength')
        self.connect('tcc.bladeWidth', 'bos.bladeWidth')
        self.connect('tcc.hubOutDiameter', 'bos.hubDiameter')
        self.connect('tcc.nacelleLength','bos.nacelleLength')
        self.connect('tcc.nacelleHeight','bos.nacelleHeight')
        self.connect('tcc.nacelleWidth','bos.nacelleWidth')
        self.connect('tcc.towerHeight', 'bos.towerLength')
        #self.connect('tcc.d_tower[0]', 'bos.maxTowerDiameter') #todo: need to correct for d_tower as an output variable
        self.connect('tcc.RNAMass', 'bos.RNAMass')
        self.connect('tcc.powerCurve', 'aep.powerCurve')
        self.connect('opex.availability', 'aep.availability')
 
        # create passthroughs for key output variables of interest
        # aep
        self.create_passthrough('aep.aepPerTurbine')
        # tcc
        self.create_passthrough('tcc.turbineMass')
        self.create_passthrough('tcc.turbine')
        # rotor
        self.create_passthrough('tcc.rotorDiameter')
        self.create_passthrough('tcc.chord_af')
        self.create_passthrough('tcc.theta_af')
        self.create_passthrough('tcc.r_af')
        self.create_passthrough('tcc.powerCurve')
        self.create_passthrough('tcc.axial_stress')
        # self.create_passthrough('tcc.soundPressureLevels')
        # drivetrain
        # tower
        self.create_passthrough('tcc.hubHeight')
        self.create_passthrough('tcc.freq')
        self.create_passthrough('tcc.stress_margin')
        self.create_passthrough('tcc.buckling_margin')
        self.create_passthrough('tcc.tip_deflection')
        self.create_passthrough('tcc.foundationMass')
        self.create_passthrough('tcc.totalSupportMass')
        # bos
        self.create_passthrough('bos.plantBOS')
        # om
        self.create_passthrough('opex.plantOM')
        self.create_passthrough('opex.availability')
        # fin
        self.create_passthrough('fin.coe')

        # passthrough inputs to tcc model
        # rotor
        self.create_passthrough('tcc.bladeNumber')
        self.create_passthrough('tcc.r')
        self.create_passthrough('tcc.chord')
        self.create_passthrough('tcc.theta')
        self.create_passthrough('tcc.precone')
        self.create_passthrough('tcc.tilt')
        self.create_passthrough('tcc.yaw')
        self.create_passthrough('tcc.maxTipSpeed')
        # drivetrain
        self.create_passthrough('tcc.gearConfig')
        self.create_passthrough('tcc.gearRatio')
        # tower / support structure
        self.create_passthrough('tcc.z_tower_height')
        self.create_passthrough('tcc.z_tower_bottom')
        self.create_passthrough('tcc.t_monopile')
        #self.create_passthrough('tcc.t_tower')
        #self.create_passthrough('tcc.d_monopile')
        #self.create_passthrough('tcc.d_tower')
    
    def execute(self):

        print "In {0}.execute()...".format(self.__class__)

        super(lcoe_cst_bos_ecn_assembly, self).execute()  # will actually run the workflow
    

if __name__=="__main__":

    lcoe = lcoe_cst_bos_ecn_assembly()

    # -- aero analysis inputs ---
    lcoe.tcc.turbinem.rotor.raero.drivetrain = csmDriveEfficiency(1)
    lcoe.tcc.advancedBlade = True # advanced blade mass closer to 5 MW reference design mass
    
    '''lcoe.execute()
    
    print "LCOE: {0}".format(lcoe.lcoe)
    print "COE: {0}".format(lcoe.coe)
    print "\n"
    print "AEP: {0}".format(lcoe.net_aep)
    print "Turbine Cost: {0}".format(lcoe.turbine_cost)
    print "BOS costs: {0}".format(lcoe.bos_cost)
    print "OnM costs per kWh: {0}".format(lcoe.avg_annual_opex / lcoe.net_aep)
    print
    print "Turbine output variable tree:"
    lcoe.turbine.printVT()
    print
    print "Plant BOS output variable tree:"
    lcoe.plantBOS.printVT()
    print
    print "Plant OM output variable tree:"
    lcoe.plantOM.printVT()
    print "Turbine power curve"
    #print lcoe.powerCurve
    #print "Sound pressure levels"
    #print lcoe.soundPressureLevels

    #lcoe = lcoe_cst_bos_ecn_assembly()'''

    #lcoe.ratedPower *= 0.9
    r = np.copy(lcoe.r)
    r[-1]*= 0.9
    lcoe.r = r
    
    lcoe.execute()
    
    print "LCOE: {0}".format(lcoe.lcoe)
    print "COE: {0}".format(lcoe.coe)
    print "\n"
    print "AEP: {0}".format(lcoe.net_aep)
    print "Turbine Cost: {0}".format(lcoe.turbine_cost)
    print "BOS costs: {0}".format(lcoe.bos_cost)
    print "OPEX costs: {0}".format(lcoe.avg_annual_opex)
    print "OnM costs per kWh: {0}".format((lcoe.avg_annual_opex - lcoe.plantOM.landLeaseCost) / lcoe.net_aep)
    print
    print "Turbine output variable tree:"
    lcoe.turbine.printVT()
    print
    print "Plant BOS output variable tree:"
    lcoe.plantBOS.printVT()
    print
    print "Plant OM output variable tree:"
    lcoe.plantOM.printVT()
    print "Turbine power curve"
    #print lcoe.powerCurve
    #print "Sound pressure levels"
    #print lcoe.soundPressureLevels

    fname = 'CST_No_OW_r9.txt'
    f = file(fname,'w')

    f.write("File Name: | {0}\n".format(fname))
    f.write("Turbine Conditions:\n")
    f.write("Rated Power: | {0}\n".format(lcoe.ratedPower))
    f.write("Rotor Diameter: | {0}\n".format(lcoe.rotorDiameter))
    f.write("Rotor maximum tip speed: | {0}\n".format(lcoe.maxTipSpeed))
    f.write("Rotor airfoil positions:\n")
    for i in range(len(lcoe.r_af)):
    	 f.write("{0}|".format(lcoe.r_af[i]))
    f.write("\n")
    f.write("Rotor chord values:\n")
    for i in range(len(lcoe.chord)):
       f.write("{0}|".format(lcoe.chord[i]))
    f.write("\n")
    f.write("Rotor chord at airfoil posiitions:\n")
    for i in range(len(lcoe.chord_af)):
    	 f.write(" {0}|".format(lcoe.chord_af[i]))
    f.write("\n")
    f.write("Rotor axial stresses along blade at airfoil positions:\n")
    for i in range(len(lcoe.axial_stress)):
       f.write("{0}|".format(lcoe.axial_stress[i]))
    f.write("\n")
    f.write("Tower lengths: |{0}| {1}\n".format(lcoe.z_tower_bottom, lcoe.z_tower_height))
    f.write("Tower diameters: |{0}| {1}\n".format(lcoe.towerBottomDiameter, lcoe.towerTopDiameter))
    f.write("Tower thickness: |{0}| {1}\n".format(lcoe.towerBottomThickness, lcoe.towerBottomDiameter))
    f.write("Tower stress margins:\n")
    for i in range(len(lcoe.stress_margin)):
    	 f.write("{0}|".format(lcoe.stress_margin))
    f.write("\n")
    f.write("Cost and mass outputs:\n")
    f.write("LCOE: |{0}\n".format(lcoe.lcoe))
    f.write("COE: |{0}\n".format(lcoe.coe))
    f.write("AEP : |{0}\n".format(lcoe.net_aep))
    f.write("Turbine Cost: |{0}\n".format(lcoe.turbine_cost))
    f.write("BOS costs : |{0}\n".format(lcoe.bos_cost))
    f.write("OPEX costs : |{0}\n".format(lcoe.avg_annual_opex))
    f.write("Turbine output variable tree:\n")
    lcoe.turbine.fwriteVT(f)
    f.write("Plant BOS output variable tree:\n")
    lcoe.plantBOS.fwriteVT(f)
    f.write("Plant OM output variable tree:\n")
    lcoe.plantOM.fwriteVT(f)
    f.write("AEP Statistics:\n")
    #f.write("Gross AEP: |{0}\n".format(lcoe.gross_aep))
    #f.write("Capacity factor: |{0}\n".format(lcoe.capacity_factor))
    f.write("Rotor Power Curve and sound output:\n")
    for i in range(len(lcoe.powerCurve[0])):
      f.write("{0} | {1} \n".format(lcoe.powerCurve[0][i],lcoe.powerCurve[1][i]))

    f.close()