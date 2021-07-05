import solsticepy
from solsticepy.design_bd import *
import numpy as np
import os


def set_param(inputs={}):
    '''
    set parameters
    '''

    pm=Parameters()
    for k, v in inputs.iteritems():

        if hasattr(pm, k):
            setattr(pm, k, v)
        else:
            raise RuntimeError("invalid paramter '%s'"%(k,))

    pm.dependent_par()
    return pm

def run_simul(inputs={}):
    '''
    design the field base on performance of annual performance
    the annual performance is TMY DNI weighted
    '''

    pm=set_param(inputs)

    print('')
    print('Test inputs')
    for k, v in inputs.iteritems():
        print(k, '=', getattr(pm, k))
    print ('')

    TIME=np.array([])
    print('')

    start=time.time()

    casedir=pm.casedir
    tablefile=casedir+'/OELT_Solstice.motab'
    if os.path.exists(tablefile):
        print('')
        print('Load exsiting OELT')

    else:
        # fixed parameters
        # =========

        pm.Q_in_rcv=40e6
        num_hst = 300
        pm.n_col_oelt=5
        pm.n_col_oelt=5
        #pm.H_rcv=H_rcv
        #pm.W_rcv=W_rcv
        pm.W_helio=6.1 # ASTRI helio size
        pm.H_helio=6.1
        pm.n_rays=int(1e6)
        pm.field_type = 'surround'
        pm.dependent_par()

        pm.Z_helio = 0.
        pm.R1 = 30.
        pm.lat = -27.16 #degree
        # enter the parameters for the beam-down components
        receiver='beam_down'
        rec_grid=20
        # 2D-crossed cpc with n faces
        n_CPC_faces=4
        n_Z=30.
        # Secondary refector 'hyperboloid'
        # parameters recalculated (pre-optimized before optimization)
        secref_vert=None #np.array([[-15,25],[-15,-25],[15,-25],[15,25]])
		# CPC and secondary mirror
        refl_sec=0.95
        slope_error=1.e-3 # radian

        pm.saveparam(casedir)
        # create the environment and scene
        # =========

        bd=BD(latitude=pm.lat, casedir=casedir)

        bd.receiversystem(receiver=receiver, rec_abs=float(pm.alpha_rcv), rec_w=float(pm.W_rcv), rec_l=float(pm.H_rcv), rec_z=float(pm.rec_z), rec_grid=int(rec_grid), cpc_nfaces=int(n_CPC_faces), cpc_theta_deg=float(pm.cpc_theta_deg), cpc_h_ratio=float(pm.cpc_h_ratio), cpc_nZ=float(n_Z), field_rim_angle=float(pm.field_rim_angle), aim_z=float(pm.H_tower), secref_inv_eccen=pm.secref_inv_eccen, secref_vert = secref_vert, refl_sec=float(refl_sec), slope_error=float(slope_error))

        bd.heliostatfield(field=pm.field_type, hst_rho=pm.rho_helio, slope=slope_error, hst_w=pm.W_helio, hst_h=pm.H_helio, tower_h=pm.H_tower, tower_r=pm.R_tower, hst_z=pm.Z_helio, num_hst=num_hst, R1=pm.R1, fb=pm.fb, dsep=pm.dsep, x_max=150., y_max=150.)

        bd.yaml(sunshape=pm.sunshape,csr=pm.crs,half_angle_deg=pm.half_angle_deg, std_dev=pm.std_dev)

        oelt, A_land=bd.field_design_annual(dni_des=900., num_rays=int(pm.n_rays), nd=int(pm.n_row_oelt), nh=int(pm.n_col_oelt), weafile=pm.wea_file, method=1, Q_in_des=pm.Q_in_rcv, n_helios=None, zipfiles=False, gen_vtk=False, plot=False)


        if (A_land==0):
            tablefile=None
        else:
            A_helio=pm.H_helio*pm.W_helio
            output_matadata_motab(table=oelt, field_type=pm.field_type, aiming='single', n_helios=bd.n_helios, A_helio=A_helio, eff_design=bd.eff_des, H_rcv=pm.H_rcv, W_rcv=pm.W_rcv, H_tower=pm.H_tower, Q_in_rcv=bd.Q_in_rcv, A_land=A_land, savedir=tablefile)


    return tablefile



if __name__=='__main__':
	case="./test"
	weafile='../../Data/Weather/example_TMY3.motab'
	cpc_theta_deg=20.
	cpc_h_ratio=1.
	field_rim_angle=80.
	secref_inv_eccen=0.6
	rec_z=0.
	W_rcv=1.2
	H_rcv=10.
	H_tower = 75.
	inputs={'casedir': case, 'wea_file': weafile, 'cpc_theta_deg': cpc_theta_deg, 'cpc_h_ratio': cpc_h_ratio, 'field_rim_angle': field_rim_angle, 'secref_inv_eccen': secref_inv_eccen, 'rec_z': rec_z, 'W_rcv':W_rcv, 'H_rcv': H_rcv, 'H_tower': H_tower}
	run_simul(inputs)
