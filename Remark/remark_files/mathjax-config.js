// Description: MathJax configuration file for Remark
// Documentation: math_syntax.txt

MathJax.Hub.Config({
    asciimath2jax: 
    {
        delimiters: [["''", "''"]]
    },
    tex2jax: 
    {   
        inlineMath: [["$","$"]],
        displayMath: [["$$", "$$"]],
        processEscapes: true
    }
});
MathJax.Hub.Configured();

