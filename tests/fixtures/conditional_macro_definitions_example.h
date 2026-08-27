#define STD_OFF 0u
#define STD_ON  1u

#define FEATURE_SELECTOR STD_OFF
#define NESTED_SELECTOR STD_ON

#if (FEATURE_SELECTOR == STD_ON)
# define FEATURE_STATE STD_ON
#elif defined(FEATURE_FALLBACK)
# define FEATURE_STATE STD_ON
#else
# define FEATURE_STATE STD_OFF
#endif

#if defined(NESTED_SELECTOR)
# if (FEATURE_SELECTOR == STD_OFF)
#  define NESTED_FEATURE_STATE STD_ON
# else
#  define NESTED_FEATURE_STATE STD_OFF
# endif
#endif

#define FUNCTION_MACRO(value) ((value) + 1)