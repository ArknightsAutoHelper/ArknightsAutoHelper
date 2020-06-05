# wrapper for swagger-codegen generated package
# command line: java -jar swagger-codegen-cli-2.4.14.jar generate -i https://penguin-stats.io/PenguinStats/v2/api-docs -l python -o penguin_stats/gen -DpackageName=penguin_client -DapiTests=false -DmodelTests=false -DmodelDocs=false -DapiDocs=false

__import__('sys').path.append((lambda path: path.dirname(path.abspath(__file__)))(__import__('os').path))
from penguin_client import *
