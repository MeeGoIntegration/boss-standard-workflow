Hello, this is a mail from the unit tests of the notify participant,
specifically the template_body variant.
You may be interested in these messages:
#for $item in $f.msg
 * $item
#end for

Another thing we want to test is that undefined workitem fields are just
replaced with empty strings. So "$f.abcdef" should be empty,
and "$f.ab.cd.ef" should also be empty.
Same for undefined request attributes like $req.abcdef
whereas id=$req.id works normally.

Thank you and have a nice day.
