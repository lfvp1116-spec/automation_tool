#include "ExampleModule.h"
#include "ExampleModule_Cfg.h"

#if (DET_DEBUG_ENABLED == STD_ON)
void Example_DebugFunction(void)
{
}
#endif

#ifdef FEATURE_X
void Example_FeatureX(void)
{
}
#endif

#if defined(INTEGRATION_TEST_VARM_TASK_PERIOD)
void Example_IntegrationTest(void)
{
}
#elif defined(TEST_MODE)
void Example_TestMode(void)
{
}
#endif

#if (DET_DEBUG_ENABLED == STD_ON) && (DET_DLTFILTERSIZE > 0)
void Example_ComplexCondition(void)
{
}
#endif