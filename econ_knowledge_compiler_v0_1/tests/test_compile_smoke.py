from econ_knowledge_compiler.util import slugify

def test_slugify():
    assert slugify("Inflation expectations") == "inflation-expectations"
    assert slugify("Dólar & inflación") == "dolar-inflacion"
