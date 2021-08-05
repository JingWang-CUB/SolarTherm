#!/usr/bin/env python
##
# The Python wrapper to call DAKOTA to perform:
# I.   Parametric study, e.g. uniform, LHS etc
# II.  Uncertainty study, e.g. Monte-Carlo, LHS etc
# III. Optimisation, e.g.
#     	(1) gradient-based
#     	(2) non-gradient-based
#     	(3) derivative-free
#     	(4) surrogate-based
#
# with multiprocessing options
# I.   Single-level parallelism, e.g.
#		(1) asychronous local parallelism
#		(2) message passing parallelism
#   	(3) hybrid parallelisim
# II.  Multi-level parallelism, e.g.
#		(1) asychronous local parallelism
#		(2) message passing parallelism
#   	(3) hybrid parallelisim

## TODO
# develop it for the uncertainty study first
# the next is to generalise it to parametric study and optimisation
# more complex parallelism is also to be developed (tested)


import os

def gen_dakota_in(response, method, variables, savedir):
	'''
	Generate dakota input file: sample.in

	Arguments:
	* `mode` (str): 'uncertainty' or 'parametric' or 'optimisation
	* `sample_type` (str): 'lhs' (i.e. Latin hyper-cube sample)
						or 'random'(i.e. MC sample)
	* `num_sample` (int): number of samples
	* `variables` (str): the variable specification in dakota
                         e.g. generated by the Uncertainty class
	* `mofn` (str): the absolute directory of the modelica file
	* `savedir` (str): directory to save the sample.in file
	'''

	sample='''
# Dakota Input File: sample.in
# Usage:
#    dakota -i sample.in -o sample.out > sample.stdout
# or if run in multi-level parallelism:
#    mpirun dakota -i sample.in -o sample.out > sample.stdout

environment
    tabular_data
    tabular_data_file = "sample.dat"

model
    single

interface
    fork
    analysis_drivers = "%s/interface_bb.py"
    parameters_file = "params.in"
    results_file = "results.out"
	file_tag
	#file_save

responses
	%s

variables
%s
method
%s
'''%(savedir, response, variables, method)


	if not os.path.exists(savedir):
		os.makedirs(savedir)
	with open(savedir+'/sample.in', 'w') as f:
		f.write(sample)


class UncertaintyDakotaIn:
	#TODO
	'''
	description and architecture
	'''
	def __init__(self, mofn, start, stop, step, initStep, maxStep, integOrder, solver, nls, lv, system, runsolstice=False, peaker=False, perf_num=1, perf_i=[1]):


		if perf_num!=len(perf_i):
			perf_num=len(perf_i)

		self.variables='	discrete_state_set\n'
		self.variables+='        string %s\n'%(14+perf_num*2)
		set_n='  "fn"  "system"  "start"  "stop"  "step"  "initStep"  "maxStep"  "integOrder"  "solver"  "nls"  "lv"  "runsolstice" "peaker" "num_perf"'
		set_v='  "%s"  "%s"  "%s"  "%s"  "%s"  "%s" "%s" "%s"  "%s"  "%s"  "%s"  "%s"  "%s" "%s"'%(mofn, system, start, stop, step, initStep, maxStep, integOrder, solver, nls, lv, runsolstice, peaker, perf_num)


		for i in range(perf_num):
			set_n+='  "index%s"'%i
			set_v+='  "%s"'%perf_i[i]

		for i in range(perf_num):
			set_n+='  "sign%s"'%i
			set_v+='  "1"'

		self.variables+='        set_values'+set_v+'\n'
		self.variables+='        descriptors'+set_n+'\n'


	def uniform(self, var_names, minimum, maximum):
		'''
		Uniform distribution

		Arguments:
			var_names, a list of string,
				   the names of the parameters that are uniform distribution
			mininum, a list of float, the lower bounds of all the parameters
			maximum, a list of float, the upper bounds of all the parameters

		'''
		var_num=len(var_names)
		lb=''
		ub=''
		descriptor=''
		self.variables+='    uniform_uncertain=%s\n'%var_num
		for i in range(var_num):
			lb+=' %s'%minimum[i]
			ub+=' %s'%maximum[i]
			descriptor+=' "%s"'%var_names[i]
		self.variables+='        lower_bounds'+lb+'\n'
		self.variables+='        upper_bounds'+ub+'\n'
		self.variables+='        descriptors'+descriptor+'\n'

	def normal(self, var_names, nominals, stdevs):
		'''
		Normal distribution

		Arguments:
			var_names, a list of string,
				   the names of the parameters that are normal distribution
			nominals, a list of float, the mean values of all the paramters
			stdevs, a list of float, the standard deviations of all the parameters

		'''
		var_num=len(var_names)
		mean=''  # mean value
		stdev='' # standard deviation
		descriptor=''
		self.variables+='    normal_uncertain=%s\n'%var_num
		for i in range(var_num):
			mean+=' %s'%nominals[i]
			stdev+=' %s'%stdevs[i]
			descriptor+=' "%s"'%var_names[i]
		self.variables+='        means'+mean+'\n'
		self.variables+='        std_deviations'+stdev+'\n'
		self.variables+='        descriptors'+descriptor+'\n'

	def pert(self, var_names, nominals, minimum, maximum, scale=4.):
		'''
		Pert-beta distribution

		Arguments:
			var_names, a list of string,
				   the names of the parameters that are pert-beta distribution
			nominals, a list of float, the mean values of all the paramters
			mininum, a list of float, the lower bounds of all the parameters
			maximum, a list of float, the upper bounds of all the parameters
			scale: TODO

		'''

		var_num=len(var_names)
		alpha=''
		beta=''
		lb=''
		ub=''
		descriptor=''
		self.variables+='    beta_uncertain=%s\n'%var_num
		for i in range(var_num):
			# convert pert to beta distribution
			xmax=maximum[i]
			xmin=minimum[i]
			x=nominals[i]

			mean=(xmin+xmax+scale*x)/(scale+2)
			if abs(mean-x)<1e-10:
				a=scale/2.+1.
			else:
				a=(mean-xmin)*(2.*x-xmin-xmax)/(x-mean)/(xmax-xmin)
			b=a*(xmax-mean)/(mean-xmin)

			alpha+=' %s'%a #TODO %s --> %.xf, check precison
			beta+=' %s'%b
			lb+=' %s'%xmin
			ub+=' %s'%xmax
			descriptor+=' "%s"'%var_names[i]

		self.variables+='        alphas'+alpha+'\n'
		self.variables+='        betas'+beta+'\n'
		self.variables+='        lower_bounds'+lb+'\n'
		self.variables+='        upper_bounds'+ub+'\n'
		self.variables+='        descriptors'+descriptor+'\n'
		return a, b

	def beta(self, a, b, lb, ub, x):
		'''
		Beta distribution, ref. DAKOTA Reference-6.10.0.pdf page3250
		'''
		from scipy.special import gamma
		B=gamma(a)*gamma(b)/gamma(a+b)
		f=(x-lb)**(a-1.)*(ub-x)**(b-1.)/B/(ub-lb)**(a+b-1)
		return f

	def method(self,sample_type, num_sample):
		m=''
		m+='    sampling\n'
		m+='        sample_type %s\n'%sample_type
		m+='        samples = %s\n'%num_sample
		return m

	def response(self):
		r='response_functions = 1\nno_gradients\nno_hessians\n'
		return r



class OptimisationDakotaIn:
	#TODO
	'''
	description
	'''
	def __init__(self):
		self.method=''

	def moga(self,seed=10983, max_eval=2500, init_type='unique_random', crossover_type='shuffle_random', num_offspring=2, num_parents=2, crossover_rate=0.8, mutation_type='replace_uniform', mutation_rate=0.1, fitness_type='domination_count', percent_change = 0.05, num_generations = 40, final_solutions = 3):

		'''
		seed, int, index of seed, to generate repeatable results
		max_eval, int, maximum function evaluations
		init_type, str, initialisation type, 'unique_random', 'simple_random' or 'flat_file'
		crossover_type, str, 'shuffle_random', 'multi_point_parameterized_binary' etc
		num_offspring
		num_parents
		final_solutions, int, the first three best solutions
		'''

		self.method+='''
    moga
        seed = %s
    max_function_evaluations = %s
    initialization_type %s
    crossover_type %s
        num_offspring = %s num_parents = %s
        crossover_rate = %s
    mutation_type %s
        mutation_rate = %s
    fitness_type %s
    replacement_type below_limit = 6
        shrinkage_fraction = 0.9
    convergence_type metric_tracker
        percent_change = %s num_generations = %s
    final_solutions = %s
    output silent
'''%(seed, max_eval, init_type, crossover_type, num_offspring, num_parents, crossover_rate, mutation_type , mutation_rate, fitness_type, percent_change, num_generations, final_solutions)

	def soga(self,seed=10983, max_eval=2000, init_type='unique_random', pop_size=48, crossover_type=None,  num_offspring=2, num_parents=2, crossover_multip=2, crossover_rate=0.8, mutation_type='replace_uniform', mutation_rate=0.2, fitness_type='merit_function', percent_change = 0.05, num_generations = 20):

		'''
		seed, int, index of seed, to generate repeatable results
		max_eval, int, maximum function evaluations
		init_type, str, initialisation type, 'unique_random', 'simple_random' or 'flat_file'
		pop_size, int, population size
		crossover_type, str, 'shuffle_random', 'multi_point_parameterized_binary' etc
		crossover_multip, int, multi_point_parameterized_binary
		num_offspring, int
		num_parents, int
		final_solutions, int, the first three best solutions
		'''
		if crossover_type=='shuffle_random':
			crossover='''crossover_type shuffle_random
        num_offspring = %s num_parents = %s
        crossover_rate = %s'''%(num_offspring, num_parents,crossover_rate)
		else:
			# multi_point_parameterized_binary
			crossover='''crossover_type
        multi_point_parameterized_binary= %s
        crossover_rate = %s'''%(crossover_multip,crossover_rate)


		self.method+='''
    soga
        seed = %s
    max_function_evaluations = %s
    initialization_type %s
	population_size=%s
    %s
    mutation_type %s
        mutation_rate = %s
    fitness_type %s
    replacement_type elitist
    convergence_type average_fitness_tracker
        percent_change = %s num_generations = %s
    output silent
'''%(seed, max_eval, init_type, pop_size, crossover, mutation_type , mutation_rate, fitness_type, percent_change, num_generations)


	def variables(self, var_names, nominals, maximum, minimum, mofn, perf_i, perf_name, perf_sign, system, start, stop, step, initStep, maxStep, integOrder, solver, nls, lv, runsolstice=False, peaker=False):

		perf_num=len(perf_sign)

		v='    discrete_state_set\n'
		v+='        string %s\n'%(14+perf_num*2)
		set_n='  "fn"  "system"  "start"  "stop"  "step"  "initStep"  "maxStep"  "integOrder"  "solver"  "nls"  "lv"  "runsolstice" "peaker" "num_perf"'
		set_v='  "%s"  "%s"  "%s"  "%s"  "%s"  "%s" "%s" "%s"  "%s"  "%s"  "%s"  "%s"  "%s"  "%s"'%(mofn, system, start, stop, step, initStep, maxStep, integOrder, solver, nls, lv, runsolstice, peaker, perf_num)


		for i in range(perf_num):
			if system=='TEST':
				set_n+='  "index%s"'%i
				set_v+='  "%s"'%perf_name[i]

			else:
				set_n+='  "index%s"'%i
				set_v+='  "%s"'%perf_i[i]

		for i in range(perf_num):
			set_n+='  "sign%s"'%i
			set_v+='  "%s"'%perf_sign[i]

		v+='        set_values'+set_v+'\n'
		v+='        descriptors'+set_n+'\n'

		var_num=len(var_names)
		init=''
		lb=''
		ub=''
		descriptor=''
		v+='    continuous_design=%s\n'%var_num
		for i in range(var_num):
			init+=' %s'%nominals[i]
			lb+=' %s'%minimum[i]
			ub+=' %s'%maximum[i]
			descriptor+=' "%s"'%var_names[i]

		v+='        initial_point'+init+'\n'
		v+='        lower_bounds'+lb+'\n'
		v+='        upper_bounds'+ub+'\n'
		v+='        descriptors'+descriptor+'\n'
		return v

	def response(self, num_obj):
		r='objective_functions = %s\nno_gradients\nno_hessians\n'%num_obj
		return r



def gen_interface_bb(savedir):
	'''
	This function generate the interface_bb.py script
	which will be excuted by DAKOTA

	* `savedir` (str): directory to save the interface_bb.py file
	* `perf_n` (list of str): a list of the names of the resulting performance, e.g. lcoe, capf, epy, srev
	* `perf_sign` (list of float): a list of signs for the optimisation, e.g. 1 is to minimise, -1 is to maximise;
								   perf_sign=None if it is a study other than optiisation
	'''


	bb='''#!/usr/bin/env python

# Dakota will execute this script
# The command line arguments will be extracted by dakota.interfacing automatically.

# load the necessary Python modeuls
import dakota.interfacing as di
import os
import glob

# Parse Dakota parameters file
params, results = di.read_parameters_file()

# obtain the modelica file name
# variable names and values
# index of the case (suffix for output)
names=params.descriptors
fn=params.__getitem__("fn") #the modelica file
system=params.__getitem__("system") # fuel system or power system
num_perf=int(params.__getitem__("num_perf")) # number of the performance results
model=os.path.splitext(os.path.split(fn)[1])[0] # model name
start=str(params.__getitem__("start"))
stop=str(params.__getitem__("stop"))
step=str(params.__getitem__("step"))
initStep=params.__getitem__("initStep")
maxStep=params.__getitem__("maxStep")
integOrder=str(params.__getitem__("integOrder"))
solver=str(params.__getitem__("solver"))
nls=str(params.__getitem__("nls"))
lv=str(params.__getitem__("lv"))

runsolstice=params.__getitem__("runsolstice")
peaker=params.__getitem__("peaker")


initStep = None if initStep == 'None' else str(initStep)
maxStep = None if maxStep == 'None' else str(maxStep)

var_n=[] # variable names
var_v=[] # variable values

print('')

print(names[:-(14+2*num_perf)])
for n in names[:-(14+2*num_perf)]:
	var_n.append(n.encode("UTF-8"))
	var_v.append(str(params.__getitem__(n)))
	print('variable   : ', n, '=', params.__getitem__(n))

# case suffix
suffix=results.results_file.split(".")[-1]


if runsolstice=='True':
	optic_folder='optic_case_%s'%suffix
	var_n.append('casefolder')
	var_v.append(optic_folder)
	print('casefolder = '+ optic_folder)


# run solartherm
from solartherm import postproc
from solartherm import simulation
sim = simulation.Simulator(fn=fn, suffix=suffix, fusemount=False)
if not os.path.exists(model):
	sim.compile_model()
	sim.compile_sim(args=['-s'])


sim.update_pars(var_n, var_v)
#sim.simulate(start=0, stop='1y', step='5m',solver='dassl', nls='newton')
#sim.simulate(start=0, stop='1y', step='1h',initStep='60s', maxStep='60s', solver='dassl', nls='newton')
sim.simulate(start=start, stop=stop, step=step, initStep=initStep, maxStep=maxStep, integOrder=integOrder, solver=solver, nls=nls, lv=lv)

try:
	if system=='TEST':
		import DyMat
		res=DyMat.DyMatFile(sim.res_fn)
	else:
		if system=='FUEL':
			resultclass = postproc.SimResultFuel(sim.res_fn)
		else:
			resultclass = postproc.SimResultElec(sim.res_fn)

		if peaker=='True':
			perf = resultclass.calc_perf(peaker=True)
		else:
			perf = resultclass.calc_perf()


	solartherm_res=[]

	for i in range(num_perf):
		sign=float(params.__getitem__("sign%s"%i))

		if system=='TEST':
			name=params.__getitem__("index%s"%i)
			solartherm_res.append(sign*res.data(name)[-1])
			print('objective %s: '%i, name, sign*res.data(name)[-1])
		else:
			idx=int(params.__getitem__("index%s"%i))
			solartherm_res.append(sign*perf[idx])
			print('objective %s: '%i, resultclass.perf_n[idx], sign*perf[idx])
except:
	solartherm_res=[]
	for i in range(num_perf):
		sign=float(params.__getitem__("sign%s"%i))
		if sign>0: #minimisation
			error=99999
		else: # maxmisation
			error=0

		solartherm_res.append(sign*error)
	print('Simulation Failed')


print('')

# Return the results to Dakota
for i, r in enumerate(results.responses()):
    if r.asv.function:
        r.function = solartherm_res[i]
results.write()

map(os.unlink, glob.glob(sim.res_fn))
#map(os.unlink, glob.glob(model+'_init_*.xml'))

'''
	if not os.path.exists(savedir):
		os.makedirs(savedir)
	with open(savedir+'/interface_bb.py', 'w') as f:
		f.write(bb)

if __name__=='__main__':
	'''
	mode='uncertainty'
	sample_type='lhs'
	num_sample=20
	dist_type='uniform'
	var_num=3
	var_names=["rec_fr","eff_blk","he_av_design"]
	var_vals=[[0.01,0.09],[0.25,0.42],[0.985,0.995]]
	mofn="/home/yewang/solartherm-master/examples/Reference_2.mo"
	savedir='/media/yewang/Data/svn_gen3p3/system-modelling/research/sensitivity-analysis-DAKOTA/test'
	gen_dakota_in(mode, sample_type, num_sample, dist_type, var_num, var_names, var_vals, mofn, savedir)
	'''
	# test the Pert-beta distribution
	# ref https://www.riskamp.com/beta-pert
	import numpy as N
	import matplotlib.pyplot as plt
	lb=0.001
	ub=0.003
	n=0.00153
	u=UncertaintyDakotaIn(None, None, None,None,None,None, None, None, None,None, None)
	a,b=u.pert(var_names=['test'], nominals=[n], minimum=[lb], maximum=[ub])
	print a, b
	X=N.linspace(lb, ub, 100)
	Y=u.beta(a, b, lb, ub, X)
	plt.plot(X, Y)
	plt.show()
	plt.close()
