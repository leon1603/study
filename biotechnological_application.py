# -*- coding: utf-8 -*-
"""biotechnological_application.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ya_PvsPsfXqG-esdc1JTqRCO4B_enutm
"""

import cbmpy
import os
import numpy as np
import pandas as pd

"""# Biotechnological application

## Isobutanol production in *E. coli*

Question: What is the biotechnological use of isobutanol?

## 1. Download the *E. coli* model iML1515 from the BiGG database and load it into the colab environment and cbmpy.

This exercise will be base on the results of [this paper](https://link.springer.com/article/10.1186/s13068-023-02395-z). An important figure of the paper is here:

"""

model = cbmpy.loadModel("iML1515.xml")

result = cbmpy.doFBA(model)


"""## Model anaerobic growth.
What is the difference in growth rate?
"""

model.setReactionBounds('R_EX_o2_e', 0, 0)

result = cbmpy.doFBA(model)

"""## Add the reactions required to make isobutanol

You can find the reactions in the BiGG database or in the kegg database.
The genes of the pathway are:
- *E. coli* ilvH and ilvI (already in the model)
- *E. coli* ilvC (already in the model)
- *E. coli* ilvD (already in the model)
- *Lactococcus lactis* kivd (https://biocyc.org/reaction?orgid=META&id=RXN-7643)
- *Clostridium Ljungdahlii* CLJU_RS08100


You also have to add transport and exchange reaction for isobutanol. Assume that isobutanol transport is energetically free.

Tip: make sure that you name the species in the reactions in the way that they are named already in the model if present.

Question: Check these genes in EcoCyc and their respective reactions, and draw the pathway that is added.

"""
### Appreciate that butanol is not a reactant in the model yet
for r in model.species:
    if r.id[2:6] == "buoh":
        print(f"found {r.id}")

# create the required butanol species
model.createSpecies('M_buoh_c', name='butanol', compartment='c')
model.createSpecies('M_buoh_p', name='butanol', compartment='p')
model.createSpecies('M_buoh_e', name='butanol', compartment='e')

### Appreciate that butanol is now a reactant in the model
for r in model.species:
    if r.id[2:6] == "buoh":
        print(f"found {r.id}")

# L lactis kivd
model.createReaction('R_KIVALDC', reversible=False, name='keto-isovalerate decarboxylase')
model.createReactionReagent('R_KIVALDC', metabolite='M_3mob_c', coefficient=-1)
model.createReactionReagent('R_KIVALDC', metabolite='M_h_c', coefficient=-1)
model.createReactionReagent('R_KIVALDC', metabolite='M_btal_c', coefficient=1)
model.createReactionReagent('R_KIVALDC', metabolite='M_co2_c', coefficient=1)
model.setReactionBounds('R_KIVALDC', 0, 1000)


# C ljungdahli ...
model.createReaction('R_ADH_BUOH', reversible=True, name='butanol specific alcohol dehydrogenase')
model.createReactionReagent('R_ADH_BUOH', metabolite='M_buoh_c', coefficient=-1)
model.createReactionReagent('R_ADH_BUOH', metabolite='M_nad_c', coefficient=-1)
model.createReactionReagent('R_ADH_BUOH', metabolite='M_nadh_c', coefficient=1)
model.createReactionReagent('R_ADH_BUOH', metabolite='M_btal_c', coefficient=1)
model.createReactionReagent('R_ADH_BUOH', metabolite='M_h_c', coefficient=1)
model.setReactionBounds('R_ADH_BUOH', -1000, 1000)

# transport
model.createReaction('R_BUTtp', reversible=True, name='butanol transport to periplasm')
model.createReactionReagent('R_BUTtp', metabolite='M_buoh_c', coefficient=-1)
model.createReactionReagent('R_BUTtp', metabolite='M_buoh_p', coefficient=1)
model.setReactionBounds('R_BUTtp', -1000, 1000)

# export
model.createReaction('R_BUTex', reversible=True, name='butanol transport to extracellular')
model.createReactionReagent('R_BUTex', metabolite='M_buoh_p', coefficient=-1)
model.createReactionReagent('R_BUTex', metabolite='M_buoh_e', coefficient=1)
model.setReactionBounds('R_BUTex', -1000, 1000)

# exchange
model.createReaction('R_EX_buoh_e', reversible=False, name='butanol exchange')
model.createReactionReagent('R_EX_buoh_e', metabolite='M_buoh_e', coefficient=-1)
model.setReactionBounds('R_EX_buoh_e', 0, 1000)

"""## Optimize butanol production

Without ATPM constraint and with ATPM constraint.
"""

model.setObjectiveFlux('R_EX_buoh_e', osense='maximize')

result = cbmpy.doFBA(model)
fluxes = model.getReactionValues()
print(fluxes['R_ATPM'])

model.setReactionBounds('R_ATPM', 0, 1000)

result = cbmpy.doFBA(model)
fluxes = model.getReactionValues()
print(fluxes['R_ATPM'])

"""Question: What conclusions can you draw from the two optimizations above (with and without ATPM constraints?)

## Optimize biomass production

Is butanol production possible while growing optimally? Perform flux variability analysis to find out at what growth rate isobutanol production will be possible (by setting the minimal growth rate to 95%, 90% etc of its maximum).

(change back the ATPM constraint if you haven't yet)
"""

model.setReactionBounds('R_ATPM', 6.86, 1000)
model.setObjectiveFlux('R_BIOMASS_Ec_iML1515_core_75p37M')
result = cbmpy.doFBA(model)
fluxes = model.getReactionValues()

print(fluxes['R_EX_buoh_e'])

var = {}
fracs = [1.0, 0.9, 0.8, 0.7, 0.6]

for f in fracs:
  model.setReactionBounds('R_BIOMASS_Ec_iML1515_core_75p37M', f*result, f*result)



  model.setObjectiveFlux('R_EX_buoh_e', osense='maximize')

  max = cbmpy.doFBA(model)

  model.setObjectiveFlux('R_EX_buoh_e', osense='minimize')
  min = cbmpy.doFBA(model)

  var[f] = [min, max]

var

"""Question: Read the code above, try to understand it and explain to each other what it does.

## What knockouts can we make to guarantee the production of isobutanol while growing?

For our bioprocess, we need both growth and production, as the cell is our biocatalyst. The bacterium will grow as fast as it can (theoretically). So our job as metabolic engineer is to find a set of knockouts that make sure that our product, isobutanol, has to be produced at the highest growth rate. This was done in [this paper](https://link.springer.com/article/10.1186/s13068-023-02395-z), in the first section of the results. In addition, pyruvate dehydrogenase (PDH) should be knocked out, as it is inactive under anaerobic conditions.

Do the knockouts and verify that at the highest growth rate, butanol production is present and is not variable.

Determine how the butanol production varies as a function of biomass production (by performing FVA).

Question: Look at the code below, 6 genes are knocked out, are these the same number that is shown on the pape, at top pane of Figure 1?. If not, what can explain the difference?
"""

model.setReactionBounds('R_BIOMASS_Ec_iML1515_core_75p37M', 0, 1000)
model.setReactionBounds('R_ACKr', 0, 0)
model.setReactionBounds('R_FRD2', 0, 0)
model.setReactionBounds('R_FRD3', 0, 0)
model.setReactionBounds('R_LDH_D', 0, 0)
model.setReactionBounds('R_LDH_D2', 0, 0)
model.setReactionBounds('R_ALCD2x', 0, 0)

# Additional knockouts not mentioned in the paper
model.setReactionBounds('R_PDH', 0, 0) # PDH is downregulated under anaerobic conditions


model.setObjectiveFlux('R_BIOMASS_Ec_iML1515_core_75p37M', osense='maximize')

result = cbmpy.doFBA(model)
fluxes = model.getReactionValues()

fluxes['R_EX_buoh_e']

"""Question: What is the difference in maximal growth between the model with and without these knockouts?"""

var = {}
fracs = [1.0, 0.9, 0.8, 0.7, 0.6]

for f in fracs:
  model.setReactionBounds('R_BIOMASS_Ec_iML1515_core_75p37M', f*result, f*result)



  model.setObjectiveFlux('R_EX_buoh_e', osense='maximize')

  max = cbmpy.doFBA(model)

  fluxes_max = model.getReactionValues()
  print('max: f = ' + str(f) + '; buoh = ' + str(max) + '; biomass = ' + str(fluxes_max['R_BIOMASS_Ec_iML1515_core_75p37M']))

  model.setObjectiveFlux('R_EX_buoh_e', osense='minimize')
  min = cbmpy.doFBA(model)
  fluxes_min = model.getReactionValues()
  print('min: f = ' + str(f) + '; buoh = ' + str(min) + '; biomass = ' + str(fluxes_max['R_BIOMASS_Ec_iML1515_core_75p37M']))
  var[f] = [min, max]

fluxes = model.getReactionValues()
var

"""Question: Interpret the results above.

## Advanced: Can you try to find knockouts that improve the butanol production, also when not growing at the optimal rate?

Tip: Look at the production and consumption of NADH.
"""
