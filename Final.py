#!/usr/bin/env python
# coding: utf-8

# In[78]:


import glob
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams
from scipy import stats


# # INDIVIDUAL RAW CSV FILE

# In[55]:


# Read raw data - Do it for all csv file name by changing the file name
df = pd.read_csv("M08.csv", sep = "|")


# In[56]:


df.drop(['DIV_NBR', 'RX_DC_ID', 'ZIP_CD', 'NDC_DSC', 'GEN_BRAND_IND', 'PKG_SIZE', 'CASE_SIZE_QTY', 'COST_BUCKET', 'TIL_PKG', 'OV_INV_QTY', 'DC_SHIP'], axis = 1, inplace = True)


# In[57]:


# Apply assumption: 
# when Inventory on hand(BOH_PKG) is 0, lost sales are about 10% of the sales that week
df["TEMP"] = np.where(df["BOH_PKG"] == 0, df["SALES_PKG"] * 1.1, df["SALES_PKG"])
df["SALES"] = np.where(df["TEMP"] < 0, 0, df["TEMP"])
df.drop(["TEMP", "SALES_PKG"], axis = 1, inplace = True)


# In[58]:


# when Inventory on hand(BOH_PKG) is less than zero, convert it to zero
# Change column name: BOH_PKG -> IOH
df["IOH"] = np.where(df["BOH_PKG"] < 0, 0, df["BOH_PKG"])
df.drop(["BOH_PKG"], axis =1, inplace = True)


# In[59]:


# Caculate average weekly sales for each SKU at each Store
wf = df.groupby([df["STORE_NBR"], df["NDC_NBR"]])["SALES"].mean().reset_index().round(3)


# In[60]:


# Filter only week 52
now = df[df["WEEK_NBR"] == 201852].reset_index()
now.drop('SALES', axis = 1, inplace = True)


# In[61]:


# merge average weekly sales value to filtered(week 52) data 
merge = pd.merge(now, wf, how = "left", left_on = ["STORE_NBR", "NDC_NBR"], right_on = ["STORE_NBR", "NDC_NBR"])


# In[66]:


# Calculate Weeks of Supply for each SKU at each store
# when average weekly sales are zero, convert to 0.00001 to calculate
merge["W_SALES"] = (np.where(merge["SALES"] == 0, 0.00001, merge["SALES"]))
merge["N_WOS"] = (merge["IOH"] / merge["W_SALES"]).round(2)
merge.drop("SALES", axis = 1, inplace = True)


# In[74]:


merge.drop(["index"], axis = 1, inplace = True)


# In[76]:


# save dataframe to csv file
merge.to_csv("WOS08.csv")


# # COMBINE MODIFIED RAW DATA

# In[79]:


# Reading all csv files created above and concatinate
df = pd.concat([pd.read_csv(f) for f in glob.glob('WOS*.csv')], ignore_index = True)
df.drop(["Unnamed: 0"], axis = 1, inplace = True)


# In[80]:


# Creating columns - target weeks of supply (3, 5, and 10)
df["TWOS03"] = 3
df["TWOS05"] = 5
df["TWOS10"] = 10


# In[81]:


# Creating columns - excess inventory in weeks
df["TEMP03"] = df["N_WOS"] - df["TWOS03"]
df["TEMP05"] = df["N_WOS"] - df["TWOS05"]
df["TEMP10"] = df["N_WOS"] - df["TWOS10"]

df["EXC_WOS03"] = np.where(df["TEMP03"] > 0, df["TEMP03"], 0)
df["EXC_WOS05"] = np.where(df["TEMP05"] > 0, df["TEMP05"], 0)
df["EXC_WOS10"] = np.where(df["TEMP10"] > 0, df["TEMP10"], 0)


# In[82]:


df.drop(["TEMP03", "TEMP05", "TEMP10"], axis = 1, inplace = True)


# In[83]:


# Convert excess inventory in weeks to excess units
df["EXC_UNIT03"] = (df["EXC_WOS03"] * df["W_SALES"]).round(3)
df["EXC_UNIT05"] = (df["EXC_WOS05"] * df["W_SALES"]).round(3)
df["EXC_UNIT10"] = (df["EXC_WOS10"] * df["W_SALES"]).round(3)


# In[84]:


# Excess units to integer - remove decimal points
df["EXC_UNIT03"] = df["EXC_UNIT03"].astype(int)
df["EXC_UNIT05"] = df["EXC_UNIT05"].astype(int)
df["EXC_UNIT10"] = df["EXC_UNIT10"].astype(int)


# In[85]:


# Creating columns - removed decimal points
df["LEFT03"] = df["IOH"] - df["EXC_UNIT03"]
df["LEFT05"] = df["IOH"] - df["EXC_UNIT05"]
df["LEFT10"] = df["IOH"] - df["EXC_UNIT10"]


# In[86]:


# Condition - leave minimum quantity at the store
# When average weekly sale is zero and excess unit is whole number, remove one unit from excess unit to leave at least one unit.
df["EXC_UNIT03"] = np.where((df["W_SALES"] < 0.0001) & (df["LEFT03"] == 0), df["EXC_UNIT03"] - 1, df["EXC_UNIT03"])
df["EXC_UNIT05"] = np.where((df["W_SALES"] < 0.0001) & (df["LEFT05"] == 0), df["EXC_UNIT05"] - 1, df["EXC_UNIT05"])
df["EXC_UNIT10"] = np.where((df["W_SALES"] < 0.0001) & (df["LEFT10"] == 0), df["EXC_UNIT10"] - 1, df["EXC_UNIT10"])


# In[87]:


# Remove unnecessary columns
df.drop(['TWOS03', 'TWOS05', 'TWOS10', 'EXC_WOS03', 'EXC_WOS05', 'EXC_WOS10'], axis = 1, inplace = True)


# # PRICE DATA FILE

# In[90]:


price = pd.read_csv("price.csv")


# In[91]:


price.drop(["Unnamed: 0", "SKU_NBR", "AWP/PKG"], axis = 1, inplace = True)


# # MERGE PRICE WITH DATA

# In[92]:


df_price = pd.merge(df, price, how = "left", left_on = "NDC_NBR", right_on ="UPC_NDC_NBR")


# In[93]:


df_price.drop(["UPC_NDC_NBR"], axis = 1, inplace = True)


# In[94]:


# Calculate excess dollar values for WOS of 3, 5, and 10
df_price["DOLLAR03"] = df_price["EXC_UNIT03"] * df_price["AWP"]
df_price["DOLLAR05"] = df_price["EXC_UNIT05"] * df_price["AWP"]
df_price["DOLLAR10"] = df_price["EXC_UNIT10"] * df_price["AWP"]

# In[95]:


# Creating new csv file
df_price.to_csv("complete.csv")


# In[96]:


df = df_price


# In[97]:


# Creating each dataframe for Q1 to Q4
q1 = df[df["WEEK_NBR"] == 201813].reset_index()
q2 = df[df["WEEK_NBR"] == 201826].reset_index()
q3 = df[df["WEEK_NBR"] == 201839].reset_index()
q4 = df[df["WEEK_NBR"] == 201852].reset_index()


# In[98]:


# Creating new csv file
q1.to_csv("201813.csv")
q2.to_csv("201826.csv")
q3.to_csv("201839.csv")
q4.to_csv("201852.csv")


# # FILTERING NON_CONTROLLED DRUGS

# In[99]:


control = pd.read_csv("control.csv")
control.drop(["Unnamed: 0", "SKU_NBR", "NDC_DSC", "PKG_SIZE", "SCHD_DRUG_CD"], axis = 1, inplace = True)


# In[100]:


# Filtering Non-Controlled drugs
# Merge Q4(week 52) dataframe with controlled & non-controlled label
merge = pd.merge(q4, control, how = "left", left_on = "NDC_NBR", right_on = "NDC_NBR")
merged = merge[merge["CONTROL_IND"] == "NON-CONTROL"].reset_index()
merged_con = merge[merge["CONTROL_IND"] == "CONTROL"].reset_index()


# # RESULT

# In[190]:


# Assigning number of top X SKUs per store
X = 20


# In[191]:


# FILTERING TOP X number of SKUs from each store
df03 = merged.groupby(["STORE_NBR"]).apply(lambda x: x.sort_values("DOLLAR03", ascending = False).head(X)).reset_index(drop = True)
df05 = merged.groupby(["STORE_NBR"]).apply(lambda x: x.sort_values("DOLLAR05", ascending = False).head(X)).reset_index(drop = True)
df10 = merged.groupby(["STORE_NBR"]).apply(lambda x: x.sort_values("DOLLAR10", ascending = False).head(X)).reset_index(drop = True)


# In[192]:


# Printing out result
print("TOP 20 dollar value products")
print("Target WOS =  3 weeks: $", (df03["DOLLAR03"].sum()/1000000).round(2), "M")
print("Target WOS =  5 weeks: $", (df05["DOLLAR05"].sum()/1000000).round(2), "M")
print("Target WOS = 10 weeks: $", (df10["DOLLAR10"].sum()/1000000).round(2), "M")
print("")
print("Total excessive dollar value (non-controlled)")
print("Target WOS =  3 weeks: $", (merged["DOLLAR03"].sum()/1000000).round(2), "M")
print("Target WOS =  5 weeks: $", (merged["DOLLAR05"].sum()/1000000).round(2), "M")
print("Target WOS = 10 weeks: $", (merged["DOLLAR10"].sum()/1000000).round(2), "M")
print("")
print("TWOS  3 -> Top 20 products are ",(((df03["DOLLAR03"].sum()/1000000)/(q4["DOLLAR03"].sum()/1000000))*100).round(2),"% of total dollar value")
print("TWOS  5 -> Top 20 products are ",(((df05["DOLLAR05"].sum()/1000000)/(q4["DOLLAR05"].sum()/1000000))*100).round(2),"% of total dollar value")
print("TWOS 10 -> Top 20 products are ",(((df10["DOLLAR10"].sum()/1000000)/(q4["DOLLAR10"].sum()/1000000))*100).round(2),"% of total dollar value")


# Below is using only Target WOS of 5 weeks


# In[160]:


SkuCount = []
Dollar = []
Percentage = []

m = merged.groupby(["STORE_NBR"])

for i in range(0, 101, 5):
    d = m.apply(lambda x: x.sort_values("DOLLAR05", ascending = False).head(i)).reset_index(drop = True)
    SkuCount.append(i)
    Dollar.append((d["DOLLAR05"].sum()/1000000).round(2))
    Percentage.append((((d["DOLLAR05"].sum())/(q4["DOLLAR05"].sum()))*100).round(2))
    
create = {"# of SKUs": SkuCount, "Dollar": Dollar, "Percentage": Percentage}
df = pd.DataFrame(create)
df



# OPERATIONAL GUIDELINE


# In[217]:


# Entire list of top 20 SKUs at each store
operation = df05.groupby(["STORE_NBR"])[["STORE_NBR", "NDC_NBR", "EXC_UNIT05", "DOLLAR05"]].head(20)
operation.head(50)


# In[218]:


operation.to_csv("operation.csv")


# In[210]:


# Specific store data
# Enter Store #
S = 3

# Return top 20 SKUs and quantities
df05[df05["STORE_NBR"] == 3][["NDC_NBR", "EXC_UNIT05", "DOLLAR05"]]


# # GRAPHS

# In[161]:


rcParams["axes.titlepad"] = 20


# In[162]:


x = SkuCount
y = DollarSave

plt.plot(x, y, "b")
plt.xlabel("# of SKUs per store shipped to mail center (units)")
plt.ylabel("Total inventory value reduction ($M)")
plt.title("Total inventory reduction by # of SKUs \n sent to mail centers by each store")


# In[163]:


x = SkuCount
y = Percentage

plt.plot(x, y, "b")
plt.xlabel("# of SKUs per store sent to mail centers (units)")
plt.ylabel("Percent of total potential inventory reduction (%)")
plt.title("Proportion of total potential inventory reduction \n by # of SKUs sent by each store to the mail centers")

# In[164]:


temp = merged.groupby(["STORE_NBR"])["NDC_NBR"].count().reset_index()
m_temp = merged[merged["EXC_UNIT05"]>0]
temp1 = m_temp.groupby(["STORE_NBR"])["NDC_NBR"].count().reset_index()


# In[165]:


plt.hist(temp["NDC_NBR"], color = 'blue', edgecolor = 'black', bins = 30)
plt.xlabel("# of SKUs per store (units)")
plt.ylabel("# of stores")
plt.title("Histogram of # of SKUs per store")


# In[179]:


print("Stores have mean of", round(temp["NDC_NBR"].mean(), 1),"SKUs with stdev of", round(temp["NDC_NBR"].std(), 1))


# In[180]:


plt.hist(temp1["NDC_NBR"], color = 'blue', edgecolor = 'black', bins = 30)
plt.xlabel("# of SKUs with excess inventory (units)")
plt.ylabel("# of stores")
plt.title("Histogram of # of SKUs with excess inventory")


# In[181]:


print("Stores have mean of", round(temp1["NDC_NBR"].mean(),1),"excess SKUs with stdev of", round(temp1["NDC_NBR"].std(),1))


# In[182]:


print("On average,", round((temp1["NDC_NBR"].mean() / temp["NDC_NBR"].mean())*100, 1),"% of SKUs are excess at each store")

