library(ggplot2)
library(ggmap)
library(rgdal)
library(scales)
library(dplyr)
library(Cairo)
library(ggsave)
library(stats)

amap <- get_map("Portland", zoom = 11, maptype = "roadmap")

afile <- read.csv("/Users/paigehurtig-crosby/Documents/ryan/pdxPropertyTrends/coords.csv")
p <- ggmap(amap) +
  geom_point(size=3, alpha=3/4, aes(lon,lat, color=Percent_Over_Valued), data=afile) + 
#  scale_color_gradient(low="blue", high="red")
   scale_color_gradientn(colors=rainbow(7))

today <- Sys.Date()
form<- format(today, format="%m-%d-%Y")

ggsave(paste("/Users/paigehurtig-crosby/Documents/ryan/pdxPropertyTrends/",as.character(form),"_pdxMap.png"), dpi=200)

