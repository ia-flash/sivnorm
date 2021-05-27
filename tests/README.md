#test post csv
curl -X POST localhost:5000/sivnorm/norm/siv_caradisiac -F 'file=@test_small.csv'
#test post json
curl 'localhost:5000/sivnorm/norm/siv_caradisiac?marque=renault&modele=clio'
