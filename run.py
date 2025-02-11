  import numpy as np
import json
import warnings
import operator

import h5py
from keras.models import model_from_json
from keras import backend as K
warnings.filterwarnings("ignore")


def read_file(file_path):
    with open(file_path, 'r') as data_file:
        data = json.loads(data_file.read())
    return data


def create_model(model_path):
    reverse_dictionary = dict((str(v), k) for k, v in dictionary.items())
    model_weights = list()
    weight_ctr = 0
    cu_wt = list()
    for index, item in enumerate(trained_model.keys()):
        if "weight_" in item:
            d_key = "weight_" + str(weight_ctr)
            weights = trained_model.get(d_key)[()]
            mean = np.mean(weights)
            cu_wt.append(mean)
            model_weights.append(weights)
            weight_ctr += 1
    print("Overall mean of model weights: %.6f" % np.mean(cu_wt))
    # set the model weights
    loaded_model.set_weights(model_weights)
    return loaded_model, dictionary, reverse_dictionary

def get_predicted_tools(base_tools, predictions, topk):
    """
    Get predicted tools. If predicted tools are less in number, combine them with published tools
    """
    intersection = list(set(predictions).intersection(set(base_tools)))
    return intersection[:topk]

def sort_by_usage(t_list, class_weights, d_dict):
    """
    Sort predictions by usage/class weights
    """
    tool_dict = dict()
    for tool in t_list:
        t_id = d_dict[tool]
        tool_dict[tool] = class_weights[str(t_id)]
    tool_dict = dict(sorted(tool_dict.items(), key=lambda kv: kv[1], reverse=True))
    return list(tool_dict.keys()), list(tool_dict.values())

def separate_predictions(base_tools, predictions, last_tool_name, weight_values, topk):
    """
    Get predictions from published and normal workflows
    """
    last_base_tools = list()
    predictions = predictions * weight_values
    prediction_pos = np.argsort(predictions, axis=-1)
    topk_prediction_pos = prediction_pos[-topk:]
    # get tool ids
    pred_tool_ids = [reverse_dictionary[str(tool_pos)] for tool_pos in topk_prediction_pos]
    if last_tool_name in base_tools:
        last_base_tools = base_tools[last_tool_name]
        if type(last_base_tools).__name__ == "str":
            # get published or compatible tools for the last tool in a sequence of tools
            last_base_tools = last_base_tools.split(",")
    # get predicted tools
    p_tools = get_predicted_tools(last_base_tools, pred_tool_ids, topk)
    sorted_c_t, sorted_c_v = sort_by_usage(p_tools, class_weights, dictionary)
    return sorted_c_t, sorted_c_v

def compute_recommendations(model, tool_sequence, labels, dictionary, reverse_dictionary, class_weights, topk=10, max_seq_len=25):
    tl_seq = tool_sequence.split(",")
    tl_seq_ids = [str(dictionary[t]) for t in tl_seq]
    last_tool_name = tl_seq[-1]
    sample = np.zeros(max_seq_len)
    weight_val = list(class_weights.values())
    weight_val = np.reshape(weight_val, (len(weight_val),))
    for idx, tool_id in enumerate(tl_seq_ids):
        sample[idx] = int(tool_id)
    sample_reshaped = np.reshape(sample, (1, max_seq_len))
    tool_sequence_names = [reverse_dictionary[str(tool_pos)] for tool_pos in tl_seq_ids]
    # predict next tools for a test path
    prediction = model.predict(sample_reshaped, verbose=0)
    nw_dimension = prediction.shape[1]
    prediction = np.reshape(prediction, (nw_dimension,))
    
    half_len = int(nw_dimension / 2)
    
    pub_t, pub_v = separate_predictions(standard_connections, prediction[:half_len], last_tool_name, weight_val, topk)
    # get recommended tools from normal workflows
    c_t, c_v = separate_predictions(compatible_tools, prediction[half_len:], last_tool_name, weight_val, topk)
    # combine predictions coming from different workflows
    # promote recommended tools coming from published workflows
    # to the top and then show other recommendations
    print()
    tool_seq_name = ",".join(tool_sequence_names)
    print("Current tool sequence: ")
    print()
    print(tool_seq_name)
    print()
    print("Overall recommendations: ")
    print()
    pub_t.extend(c_t)
    pub_v.extend(c_v)
    # remove duplicates if any
    pub_t = list(dict.fromkeys(pub_t))
    pub_v = list(dict.fromkeys(pub_v))
    print(pub_t)
    ids_tools = dict()
    for key in pub_t:
        ids_tools[key] = dictionary[key]
    print()
    print("Recommended tool ids:")
    print()
    for i in ids_tools:
        rev_id = dictionary[i]
        wt = class_weights[str(rev_id)]
        print(i + "(" + str(ids_tools[i]) + ")" + "(" + str(wt) + ")")

if __name__=="__main__":
    model_path = "data/tool_recommendation_model.hdf5"
    trained_model = h5py.File(model_path, 'r')
    model_config = json.loads(trained_model.get('model_config')[()])
    dictionary = json.loads(trained_model.get('data_dictionary')[()])
    class_weights = json.loads(trained_model.get('class_weights')[()])
    standard_connections = json.loads(trained_model.get('standard_connections')[()])
    compatible_tools = json.loads(trained_model.get('compatible_tools')[()])
    loaded_model = model_from_json(model_config)
    model, dictionary, reverse_dictionary = create_model(model_path)

    topk = 10 # set the maximum number of recommendations
    # Give tools ids in a sequence and see the recommendations. # To know all the tool ids, 
    # please print the variable 'reverse_dictionary'
    tool_seq = "trimmomatic"
    compute_recommendations(model, tool_seq, "", dictionary, reverse_dictionary, class_weights, topk)

