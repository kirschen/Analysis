#include <string>
#include <functional>
#include <vector>
#include <ctime>
#include <iostream>
#include <cstdlib>
#include <algorithm>
#include <cassert>

#include "TString.h"

#include "Analysis/TopReco/interface/utils.h"





const std::string common::CMSSW_BASE()
{
    const char* cmssw_base = std::getenv("CMSSW_BASE");
    if (!cmssw_base) {
        std::cerr << "Error! Environmental variable CMSSW_BASE not set!\n"
                  << "Please run cmsenv first.\n"
                  << "When running without CMSSW, you still need this variable so that the\n"
                  << "certain files can be found.\n";
        exit(1);            
    }
    std::string result(cmssw_base);
    return result;
}



const std::string common::DATA_PATH_COMMON()
{
    std::string result(CMSSW_BASE());
    result.append("/src/Analysis/TopReco/data");
    return result;
}



/// Get current date/time as string, format is YYYY-MM-DD_HH-mm-ss
std::string common::timestampToString(const time_t& timeAndDate)
{
    char results[100];
    if(strftime(results, sizeof(results), "%Y-%m-%d_%Hh%Mm%Ss", localtime(&timeAndDate)) == 0) assert(0);
    return results;
}



std::function<bool(const std::string& s)> common::makeStringCheck(const std::vector<TString> v_string)
{
    return [v_string](const std::string& test) -> bool {
        const TString tTest(test);
        return std::find(begin(v_string), end(v_string), tTest) != end(v_string);
    };
}



std::function<bool(const std::string& s)> common::makeStringCheckBegin(const std::vector<TString> v_string)
{
    return [v_string](const std::string& test) -> bool {
        const TString tTest(test);
        for(const auto& string : v_string){
            if(string == ""){
                if(tTest == "") return true;
                else return false;
            }
            else if(tTest.BeginsWith(string)) return true;
        }
        return false;
    };
}





