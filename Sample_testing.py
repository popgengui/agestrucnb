## function to calculate a N0 from an Nb an Nb/Nc Ratio and a lifetable
#praram Nb:  the desired Nb
#param NbNcRatio: the ratio Nb/Nc
#param maleSurvival: a list of the male survival rates for each age
#param femaleSurvival: a list of the female survival rates for each age
#param MRatio: the percentage of males in the recruitment cohort represented as a float such that 0<MRatio<1

def calcN0(Nb, NbNcRatio, maleSurvival, femaleSurvial, MRatio):
    FRatio = 1-MRatio
    Nc = Nb/NbNcRatio
    currentMaleProp=MRatio
    currentFemaleProp= FRatio
    cumPopPorp = 1
    #Assumes male and female survivals have same length
    for age in range(len(maleSurvival)):
        #calcualte new male Ratio
        currentMaleProp = currentMaleProp*maleSurvival[age]
        #calculate new female ratio
        currentFemaleProp = currentFemaleProp*femaleSurvial[age]
        #add to cumulative
        cumPopPorp+=currentMaleProp
        cumPopPorp+= currentFemaleProp
    #calulate N0
    N0 = Nc/cumPopPorp
    return N0


print calcN0(50,0.144,[0.142,0.124],[0.142,0.124],0.5)
print calcN0(20,0.144,[0.142,0.124],[0.142,0.124],0.7)

print calcN0(20,0.144,[0.144,0.126],[0.140,0.122],0.5)
print calcN0(20,0.144,[0.144,0.126],[0.140,0.122],0.6)
print calcN0(20,0.144,[0.144,0.126],[0.140,0.122],0.4)



