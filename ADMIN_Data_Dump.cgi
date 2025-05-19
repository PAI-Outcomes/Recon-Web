#______________________________________________________________________________
#
# Jay Herder
# Date: 01/15/2015
# ADMIN_PCWNR_Archive_Status_Tool.cgi
#______________________________________________________________________________

use File::Basename;
use Time::Local;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1; # don't buffer output
#______________________________________________________________________________
#
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG    = "$prog" . "$ext";
$nbsp = "&nbsp;";

################$testing++;

#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#
$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$INNCPDP    = $in{'INNCPDP'};
$DATATYPE   = $in{'DATATYPE'};
$DATAENV    = $in{'DATAENV'};
$DATERANGE  = $in{'DATERANGE'};
$DATEFROM   = $in{'DATEFROM'};
$DATETO     = $in{'DATETO'};
$Submit     = $in{'Submit'};

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;
   exit(0);
}

#______________________________________________________________________________

&hasAccess($USER);

if ( $ReconRx_Admin_Data_Dump !~ /^Yes/i ) {
   print qq#<p class="yellow"><font size=+1><strong>\n#;
   print qq#$prog<br><br>\n#;
   print qq#<i>You do not have access to this page.</i>\n#;
   print qq#</strong></font>\n#;
   print qq#</p><br>\n#;
#  print qq#<a href="Login.cgi">Log In</a><P>\n#;
   print qq#<a href="javascript:history.go(-1)"> Go Back </a><br><br>\n#;

   &trailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

print qq#
<script>
\$(document).ready(function() {
    
    \$("input[name\$=DATERANGE]").change(function() {
        var test = \$(this).val();
        \$(".hide").hide();
        \$("\#" + test).show();
    });
    \$("input[name\$=DATERANGE]:checked").change();
});
</script>
\n#;

#______________________________________________________________________________

print qq#
<script>
// Listen for click on toggle checkbox
\$(document).ready(function() {
  \$('\#select-all').click(function(event) {   
    // alert('HELLO');
    if(this.checked) {
      \$(':checkbox').each(function() {
          this.checked = true;
      });
    }
    else {
      \$(':checkbox').each(function() {
            this.checked = false;
      });
    }
  });
});
</script>
\n#;

#______________________________________________________________________________

if ( $testing ) {
  print "<br>\ntesting flag on... FATAL: FIX ME!!!!!!!!!!!!!!!!!!!!!!!! <br>\n";

  ########################################
  # BEG - TESTING SECTION SETUP
  ########################################
  
  $JJJ = $DBNAMES{"RADBNAME"};
  print "JJJ: $JJJ<br>\n" if ($debug);
  
  $WHICHDB = "Testing";		# Valid Values: "Testing" or "Webinar"
  &set_Webinar_or_Testing_DBNames;
  
  $HHH = $DBNAMES{"RADBNAME"};
  print "HHH: $HHH<br>\n" if ($debug);
  
  ########################################
  # END - TESTING SECTION SETUP
  ########################################

  $SENDTO   = "sdowning\@pharmassess.com";

} else {
  $SENDTO   = "sdowning\@pharmassess.com, bprowell\@pharmassess.com";
}

$dbin   = "RIDBNAME";
$DBNAME = $DBNAMES{"$dbin"};	"ReconRxDB";
$TABLE  = $DBTABN{"$dbin"};  	"incomingtb";

#______________________________________________________________________________

#______________________________________________________________________________
# Create the inputfile format name

my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$dateran= sprintf("%04d%02d%02d_%02d%02d", $year, $month, $day, $hour, $min);
$TCodeDate = sprintf("%04d-%02d-%02d", $year, $month, $day);

print "\nProg: $prog &nbsp; &nbsp;<br>Date: $tdate &nbsp; Time: $ttime<P>\n" if ($debug);

($title = $prog) =~ s/_/ /g;
$title =~ s/PCWNR/Post Check With No Remit/gi;
print qq#<H2>$title</H2><br>\n#;

#______________________________________________________________________________
 
$colspan = 3;
$FMTA = "%04d-%02d-%02d";
$FMT8 = "%04d%02d%02d";

my ($ncpdp, $name) = split("-", $INNCPDP, 2);
$ncpdp =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white space

$csvname  = "${prog}_${ncpdp}_${DATAENV}_${DATATYPE}_";
if ( $DATERANGE =~ /Range/i ) {
   my ($FRmon, $FRday, $FRyear) = split("/", $DATEFROM, 3);
   my ($TOmon, $TOday, $TOyear) = split("/", $DATETO,   3);
   if ( $DATAENV =~ /Aging/i ) {
      $DF = sprintf("$FMTA", $FRyear, $FRmon, $FRday);
      $DT = sprintf("$FMTA", $TOyear, $TOmon, $TOday);
   } else {
      $DF = sprintf("$FMT8", $FRyear, $FRmon, $FRday);
      $DT = sprintf("$FMT8", $TOyear, $TOmon, $TOday);
   }
   $csvname .= "${DF}_to_${DT}";
} else {
   $csvname .= "$DATERANGE";
}
$csvname .= ".csv";
if ( $csvname =~ /__/ ) {
   $csvname = $nbsp;
}

$savecsvpath = "D:/Recon-Rx/Reports/";
$csvURL      = "/reports/$csvname";
$newcsv      = $savecsvpath.$csvname;
unlink "$newcsv"   if ( -e "$newcsv" );

if ( $debug ) {
   print "\n\nDBNAME: $DBNAME, TABLE: $TABLE<br>\n";
}

%attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error );
$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd, \%attr) || &handle_error;
   
DBI->trace(1) if ($dbitrace);

#______________________________________________________________________________

my ($ENV) = &What_Env_am_I_in;

$numberofarrays = 0;
$URLH = "${prog}${ext}";
$FMT = "%0.02f";
$unique  = 10000;
%REPFIELDS = ();

&readPharmacies;
&readThirdPartyPayers;

if ( $Submit =~ /Submit/i ) {
   &doACTION;
}

print qq#<table class="main" border=1>\n#;

&DisplayData;

print "</table>\n";

#______________________________________________________________________________

# Close the Database

$dbx->disconnect;

#______________________________________________________________________________


my $end = time();
$elapsed = $end - $start;
print "<hr>Time elapsed: $elapsed seconds<hr>\n";

# &MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub DisplayData {
  print qq#<link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />\n#;
  print qq#<script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>\n#;
  print qq#<script src="/includes/jquery.maskedinput.min.js" type="text/javascript"></script>\n#;
  
  print qq#<script>\n#;
  print qq#\$(function() {\n#;
  print qq#\$( ".datepicker" ).datepicker();\n#;
  print qq#\$( "\#anim" ).change(function() {\n#;
  print qq#\$( ".datepicker" ).datepicker( "option", "showAnim", \$( this ).val() );\n#;
  print qq#});\n#;
  print qq#});\n#;
  print qq#</script>\n#;
  
  print qq#<script type="text/javascript">\n#;
  print qq#jQuery(function(\$) {\n#;
  print qq#      \$(".datepicker").mask("99/99/9999");\n#;
  print qq#   });\n#;
  print qq#</script>\n#;
 
  print qq#<FORM ACTION="$URLH" METHOD="POST">\n#;
  print qq#<INPUT TYPE="hidden" NAME="debug"   VALUE="$debug">\n#;
  print qq#<INPUT TYPE="hidden" NAME="verbose" VALUE="$verbose">\n#;

  print qq#<table border=1 cellspacing=3 cellpadding=3>\n#;
  print qq#<tr><th colspan=$colspan>Data Dump</th></tr>\n#;
  if ( $testing) {
     print "<tr><th colspan=$colspan><font size=+1 color=red>TESTING!!!!!</font></th></tr>\n";
     print "<tr><th colspan=$colspan><hr color=red></th></tr>\n";
  }
  print qq#<tr>\n#;
#--------------------
  print qq#<td>Pick an NCPDP:</td>#;
  print qq#<td colspan=2>#;
  print qq#<SELECT NAME="INNCPDP">\n#;
  foreach $key (sort { $HASHPharmacies{$a} cmp $HASHPharmacies{$b} } keys %HASHPharmacies) {
    ($id, $name) = split(" - ", $key, 2);
    if ( $key =~ /$INNCPDP/ ) {
       $SEL = "SELECTED";
    } else {
       $SEL = "";
    }
    print qq#<OPTION VALUE="$key" $SEL>$key</OPTION>\n#;
  }
  print qq#</SELECT>\n#;
  print qq#</td></tr>\n#;

#--------------------
  $SELDATAENVP  = "";
  $SELDATAENVA  = "";
  if ( $DATAENV =~ /PROD/i ) {
     $SELDATAENVP = "checked";
  } else {
     $SELDATAENVA = "checked";
  }
  print qq#<tr><td>Pick a Data Env:</td>#;
  print qq#<td width=300>#;
  print qq#<INPUT TYPE="RADIO" NAME="DATAENV" VALUE="PROD" $SELDATAENVP> Prod\n#;
  print qq#</td><td width=300>#;
  print qq#<INPUT TYPE="RADIO" NAME="DATAENV" VALUE="ARCH" $SELDATAENVA> Archive\n#;
  print qq#</td></tr>\n#;

#--------------------
  $SELDATATYPEA  = "";
  $SELDATATYPE8  = "";
  if ( $DATATYPE =~ /AGING/i ) {
     $SELDATATYPEA = "checked";
  } else {
     $SELDATATYPE8 = "checked";
  }
  print qq#<tr><td>Pick a Data Type:</td>#;
  print qq#<td>#;
  print qq#<INPUT TYPE="RADIO" NAME="DATATYPE" VALUE="AGING" $SELDATATYPEA> Aging\n#;
  print qq#</td><td>#;
  print qq#<INPUT TYPE="RADIO" NAME="DATATYPE" VALUE="835"   $SELDATATYPE8> 835\n#;
  print qq#</td></tr>\n#;

#--------------------
  $SELDATERANGEA = "";
  $SELDATERANGEN = "";
  if ( $DATERANGE =~ /Range/i ) {
     $SELDATERANGEN = "checked";
  } else {
     $SELDATERANGEA = "checked";
  }
  print qq#<tr>\n#;
  print qq#<td>Pick a Date Range:</td>\n#;
  print qq#<td>#;
  print qq#<INPUT TYPE="RADIO" NAME="DATERANGE" id="AllCheck" VALUE="ALL"   $SELDATERANGEA> ALL\n#;
  print qq#</td><td>#;
  print qq#<INPUT TYPE="RADIO" NAME="DATERANGE" id="DRCheck"  VALUE="Range" $SELDATERANGEN> Range\n#;
  print qq#</td></tr>\n#;

#--------------------
  $TROPTS = qq#id="Range" class="hide" style="display:none\;"#;
  print qq#<tr $TROPTS>\n#;
  print qq#<td>Pick Dates:</td>\n#;
  print qq#<td>From: #;
  print qq#<INPUT class="datepicker" TYPE="text" NAME="DATEFROM" VALUE="$DATEFROM" >\n#;
  print qq#</td><td>To: #;
  print qq#<INPUT class="datepicker" TYPE="text" NAME="DATETO"   VALUE="$DATETO"   >\n#;
  print qq#</td></tr>\n#;

#--------------------
  print qq#<tr>\n#;
  print qq#<td>Generated CSV:</td>\n#;
  print qq#<td colspan=2><a href="$csvURL" target=_Blank>$csvname</a></td>\n#;
  print qq#</td></tr>\n#;
#--------------------

  print qq#<tr><th colspan=$colspan><INPUT style="background-color:\#FF0; padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="Submit"></th></tr>\n#;

  print qq#</table>\n#;

  print qq#</FORM>\n#;

}

#______________________________________________________________________________

sub doACTION {
# RI: ReconRxDB.incomingtb
# RA: ReconRxDB.incomingtb_archive
# R8: ReconRxDB.835remitstb
# P8: ReconRxDB.835remitstb_archive

  $HASH   = "HASH";
  $XXFIELDS = "DBFLDS";
  $XXFIELDS = "";

  if ( $DATAENV =~ /Prod/i ) {
     if ( $DATATYPE =~ /Aging/i ) {
        $TABLE = "Incomingtb";
     } else {
        $TABLE = "835remitstb";
     }
  } else {
     if ( $DATATYPE =~ /Aging/i ) {
        $TABLE = "Incomingtb_archive";
     } else {
        $TABLE = "835remitstb_archive";
     }
  }

#-----
  $sql = "SELECT * FROM $DBNAME.$TABLE WHERE 1=0\;";
  my $sth0 = $dbx->prepare("SELECT * FROM $DBNAME.$TABLE WHERE 1=0;");
  $sth0->execute;
  my @colsn = @{$sth0->{NAME}}; # or NAME_lc if needed
  my @colst = @{$sth0->{mysql_type_name}};
  $ptr = 0;
  print "Column Name | Type<br>\n" if ($debug);
  foreach my $key ( @colsn ) {
    $$HASH{$key} = $colst[$ptr];
    printf( "%s | %s<br>\n", $key, $colst[$ptr] ) if ($debug);
    $$XXFIELDS .= qq#$key, #;
    $ptr++;
  }
  $$XXFIELDS =~ s/, $//;    # remove trailing ", "
  $sth0->finish;

  if ( $debug ) {
     print "<hr>\n";
     print "XXFIELDS:<br>$$XXFIELDS<hr>\n";
     print "<hr>\n";
  }

#-----

  $sql  = qq# SELECT $$XXFIELDS FROM $DBNAME.$TABLE #;
  if ( $DATERANGE =~ /Range/i ) {
     if ( $DATATYPE =~ /Aging/i ) {
        $sql .= qq# WHERE dbNCPDPNumber = $ncpdp && #;
        $sql .= qq# ( dbDateOfService >= '$DF' && dbDateOfService <= '$DT' ) #;
     } else {
        $sql .= qq# WHERE R_TS3_NCPDP = $ncpdp && #;
        $sql .= qq# ( R_DTM02_Date >= $DF && R_DTM02_Date <= $DT ) #;
     }
  }
  
  print "<br>doACTION Update sql:<br>\n$sql<br><br>\n" if ($debug);
  
  $sthx = $dbx->prepare($sql);
  $sthx->execute();
  
  $NumOfRows = $sthx->rows;
  print "Number of rows updated: $NumOfRows<br>\n" if ($debug);

  if ( $NumOfRows > 0 ) {
     open(CSV, "> $newcsv") || die "Couldn't open output file '$newcsv'\n\t$!\n\n";
     print CSV "$$XXFIELDS\n";
     while ( my @row = $sthx->fetchrow_array() ) {
        print CSV qq#"#;
        print CSV join('","', @row);
        print CSV qq#"\n#;
     }
     close(CSV);
  }
   
  print "<hr>\n" if ($debug);
  $sthx->finish();

  if ( $debug ) {
     print "sub doACTION. Exit.<br>\n";
     print "<hr size=8 color=blue><br>\n";
  }

}

#______________________________________________________________________________
