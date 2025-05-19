use File::Basename;
use Time::Local;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Excel::Writer::XLSX;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$ACTION     = $in{'ACTION'};
$Notes      = $in{'Notes'};
$TCode      = $in{'TCode'};

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
#;

#______________________________________________________________________________

if ( $testing ) {
  print "<br><br>\ntesting flag on... FATAL: FIX ME!!!!!!!!!!!!!!!!!!!!!!!! <br><br>\n";

  ########################################
  # BEG - TESTING SECTION SETUP
  ########################################
  
    $JJJ = $DBNAMES{"RNDBNAME"}; print "JJJ: $JJJ<br>\n";
  
    $WHICHDB = "Testing";		# Valid Values: "Testing" or "Webinar"
    &set_Webinar_or_Testing_DBNames;
  
    $HHH = $DBNAMES{"RNDBNAME"}; print "HHH: $HHH<br>\n";
  
  ########################################
  # END - TESTING SECTION SETUP
  ########################################

  $SENDTO   = "jherder\@pharmassess.com";
} else {
  $SENDTO   = "jherder\@pharmassess.com, josh\@pharmassess.com";
}

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

($title = $prog) =~ s/_/ /g;
$title =~ s/PCWNR/Post Check With No Remit/gi;
print qq#<H2>$title</H2><br>\n#;

#______________________________________________________________________________

$dbin     = "RNDBNAME";
$DBNAME   = $DBNAMES{"$dbin"};	"ReconRxDB";
$TABLE    = $DBTABN{"$dbin"};  	"PaymentNoRemit";
$dbin     = "PADBNAME";
$PADBNAME = $DBNAMES{"$dbin"};	"ReconRxDB";
$PATABLE  = $DBTABN{"$dbin"};  	"PaymentNoRemit_Archive";

$RNDBNAME = "testing" if ( $testing );
$PADBNAME = "testing" if ( $testing );

%attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error );
$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd, \%attr) || &handle_error;
   
DBI->trace(1) if ($dbitrace);

#______________________________________________________________________________

my ($ENV) = &What_Env_am_I_in;

$numberofarrays = 0;
$URLH = "${prog}${ext}";
$FMT = "%0.02f";
$colspan = 9;
$unique  = 10000;
%REPFIELDS = ();
&inithashes;

$saveformpath = "D://Recon-Rx/Reports/";
$newcsvname   = "PostCheckwithNoRemits_${dateran}.csv";
$newExcelname = "PostCheckwithNoRemits_${dateran}.xlsx";
$newcsv       = $saveformpath.$newcsvname;
$newExcel     = $saveformpath.$newExcelname;
unlink "$newcsv"   if ( -e "$newcsv" );
unlink "$newExcel" if ( -e "$newExcel" );


&readPharmacies;
&readThirdPartyPayers;
&read_first_remit_dates_table;	# jlh. 08/23/2016. Added
&GatherDataPCWNR;

if ( $ACTION !~ /^\s*$/ ) {
   print "<hr>CALL doACTION($ACTION, $TCode, $Notes)<hr><br>\n" if ($debug);
   &doACTION($ACTION, $TCode, $Notes);
   &inithashes;
   &GatherDataPCWNR;	# Yes, do a second time to pick up the updates from doACTION...
}

&display_Excel_if_exists;

print qq#<table class="main" border=1>\n#;
print "<tr><th colspan=$colspan><font size=+1 color=red>TESTING!!!!!</font></th></tr>\n" if ( $testing);

&DisplayData;

print "</table>\n";

#______________________________________________________________________________

# Close the Database

$dbx->disconnect;

#______________________________________________________________________________


my $end = time();
$elapsed = $end - $start;
print "<hr>Time elapsed: $elapsed seconds<hr>\n";

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub GatherDataPCWNR {
  $numberofarrays = 8;
  
  $sql  = qq# SELECT Pharmacy_ID, NCPDP, DateAdded, BIN, ThirdParty, PaymentType, CheckNumber, #;
  $sql .= qq# CheckAmount, CheckDate, CheckReceivedDate, Notes FROM $DBNAME.$TABLE #;
  $sql .= qq# WHERE (1=1) #;
  $sql .= qq# && NCPDP NOT IN ("1111111", "2222222") # if ($ENV !~ /DEV/i );
  $sql .= qq# ORDER BY NCPDP, ThirdParty, PaymentType #;
  
  ($sqlout = $sql) =~ s/\n/<br>\n/g;
  
  $sthx = $dbx->prepare($sql);
  $sthx->execute();
  
  my $NumOfRows = $sthx->rows;
  
  if ( $NumOfRows > 0 ) {
    while ( my @row = $sthx->fetchrow_array() ) {
       my ( $Pharmacy_ID, $NCPDP, $DateAdded, $BIN, $ThirdParty, $PaymentType, $CheckNumber, $CheckAmount, $CheckDate, $CheckReceivedDate, $Notes) = @row;
       $NCPDP = substr("0000000" . $NCPDP, -7);
       $PharmName = $Pharmacy_Names{$Pharmacy_ID};
       my $FLAG = "";
       if ( $PaymentType =~ /CHK/i && $CheckNumber =~ /^\s*$/ ) {
          $FLAG .= "Fix CheckNumber. ";
       }
       if ( $CheckDate =~ /\\./ || $CheckDate < 20100000 || $CheckDate > 20200000 || $CheckDate !~ /^\s*20/ ) {
          $FLAG .= "Fix CheckDate. ";
       }
       if ( $CheckNumber =~ /\// ) {
          $FLAG .= "Fix CheckNumber. ";
       }

       my $OCheckAmount = "\$" . &commify(sprintf("$FMT", $CheckAmount));
       $key = "$NCPDP##$CheckNumber##$CheckAmount";

       $NCPDPs{$key}       = $NCPDP;
       $PharmNames{$key}   = $PharmName;
       $TPPs{$key}         = $ThirdParty;
       $CheckNumbers{$key} = $CheckNumber;
       $CheckAmounts{$key} = $OCheckAmount;
       $CheckDates{$key}   = $CheckDate;
       $DateAddeds{$key}   = $DateAdded;
       $PaymentTypes{$key} = $PaymentType;
       $Notes{$key}        = $Notes;
       $FLAGs{$key}        = $FLAG;

    }

  } else {
    print "No entries found!<br>\n";
  }
  
  $sthx->finish;
}

#______________________________________________________________________________

sub DisplayData {
  @arrays = (
 "NCPDPs",
 "DateAddeds",
 "TPPs",
 "PaymentTypes",
 "CheckNumbers",
 "CheckAmounts",
 "CheckDates",
 "Notes");
#
  print qq#<FORM ACTION="$URLH" METHOD="POST">\n#;
  $linesprinted = 0;

  &print_headers;

# sort by NCPDP, TPP, then Check Amounts

  $CURNCPDP = 0;
  foreach $Okey (sort {
      $PharmNames{$NCPDPs{$a}} cmp $PharmNames{$NCPDPs{$b}} ||
      $NCPDPs{$a} <=> $NCPDPs{$b} ||
      $TPPs{$a} cmp $TPPs{$b} ||
      $CheckAmounts{$a} <=> $CheckAmounts{$b}
    } keys %NCPDPs) {


    $NCPDP         = $NCPDPs{$Okey};
    $Pharmacy_Name = $PharmNames{$Okey};

#    print "$Okey - $Pharmacy_Name<br>";
#   $CURNCPDP      = $NCPDPs{$Okey} if ( $CURNCPDP == 0 );

    if ( $CURNCPDP != $NCPDPs{$Okey} ) {
       $placement = $colspan-1;
       $useNCPDP = sprintf("%07d", $NCPDPs{$Okey});

       if ($ENV !~ /DEV/i ) {
          $URLREMIT = "http://dev.recon-rx.com/tools/datatracking.php?ncpdp=$useNCPDP";
       } else {
          $URLREMIT = "http://www.recon-rx.com/tools/datatracking.php?ncpdp=$useNCPDP";
       }
#      print qq#<tr><th colspan=$colspan><hr size=4 noshade color="black"></th></tr>\n#;
       print qq#<tr><th colspan=$colspan>$nbsp</th></tr>\n#;

       print qq#<tr class="grey"><th colspan=$placement>#;
       print qq#<a href="\#anchor1"><img src="/images/down53.png"></a>$nbsp#;
       print qq#$Pharmacy_Name</th>#;
       print qq#<th nowrap><a href="$URLREMIT" target=_blank">View 1st remit data</a></th>#;
       print qq#</tr>\n#;
       $CURNCPDP = $NCPDPs{$Okey};
    }

    $PCNR = "$NCPDPs{$Okey}##$PharmNames{$Okey}##$TPPs{$Okey}##$CheckNumbers{$Okey}##$CheckAmounts{$Okey}##$CheckDates{$Okey}##$DateAddeds{$Okey}##$Notes{$Okey}##$FLAGs{$Okey}";

#   print the "WHITE Lines"

    $WHITE   = "";
    $unique++;

    print qq#<tr>#;
    $NAME = "PCNR-${unique}";
    #print "NAME: $NAME<br>\n";
    print qq#<td><input type="checkbox" name="$NAME" id="$NAME" value="$PCNR"></td>\n#;
    foreach $array (@arrays) {
       $val = $$array{$Okey};
#      print "<hr>array: $array, val: $val<br>\n";
       if ( $array =~ /Check/i ) {
          $ALIGN = qq#align="right"#;
       } elsif ( $array =~ /FLAG/i ) {
          $ALIGN = qq#colspan=2#;
       } else {
          $ALIGN = "";
       }
       print "<td $ALIGN>$val</td>";
       $WHITE .= "$val##";
    }
    print "</tr>\n";
#   print "<tr><td $ALIGN>1. $WHITE</td></tr>";
    $val = $PaymentTypes{$Okey};
#   print "Payment Type: $val<br>\n";
    $WHITE .= "$val##";
    $WHITE =~ s/##\s*$//g;
#   print "<tr><td $ALIGN>2. $WHITE</td></tr>";

    $linesprinted++;
    $CHECKNUMBER = $CheckNumbers{$Okey};
    $CHECKAMOUNT = $CheckAmounts{$Okey};
    $CHECKAMOUNT =~ s/\$|,//g;
  }

  $SELADDNOTE = "";
  $SELARCHIVE = "";
  $SELEXPORT  = "";

  if ( $ACTION =~ /ADDNOTE/i ) {
     $SELADDNOTE = "checked";
  } elsif ( $ACTION =~ /ARCHIVE/i ) {
     $SELARCHIVE = "checked";
  } elsif ( $ACTION =~ /EXPORT/i ) {
     $SELEXPORT  = "checked";
  } else {
     $SELADDNOTE = "checked";
  }
  print qq#<tr><th colspan=$colspan><hr size=4 noshade color="black"></th></tr>\n#;
  print qq#<tr><th colspan=$colspan>\n#;
  print qq#  <table>\n#;
  print qq#  <tr valign="top"><td>\n#;
  print qq#<a name="anchor1" id="anchor1"></a>\n#;
  print qq#      <strong><i>Notes:</i></strong><br>\n#;
  print qq#      <TEXTAREA NAME="Notes" COLS=40 ROWS=6 WRAP="Soft">$Notes</TEXTAREA>\n#;
  print qq#  </td>\n#;
  print qq#  <td style="border-left: 1px solid \#000";>\n#;
  print qq#      <strong><i>Archive/TCode:</i></strong><br>\n#;
  print qq#      <TEXTAREA NAME="TCode" COLS=40 ROWS=1 WRAP="Soft">$TCode</TEXTAREA>\n#;
  print qq#  </td></tr>\n#;
  print qq#  </table>\n#;
  print qq#</th></tr>\n#;

  print qq#<tr><th colspan=$colspan>\n#;
  print qq#<input type="radio" name="ACTION" value="ADDNOTE" $SELADDNOTE> ADD/Update NOTE \n#;
  print qq#<input type="radio" name="ACTION" value="ARCHIVE" $SELARCHIVE> ARCHIVE \n#;
  print qq#<input type="radio" name="ACTION" value="EXPORT"  $SELEXPORT > Export\n#;

  print qq#<INPUT TYPE="hidden" NAME="USER"  VALUE="$USER">\n#;
  print qq#<INPUT TYPE="hidden" NAME="OWNER" VALUE="$OWNER">\n#;

  print qq#<INPUT style="background-color:\#FF0; padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="Submit">\n#;

  print qq#</th></tr>\n#;
  print qq#</FORM>\n#;

}

#______________________________________________________________________________

sub print_headers {
  print qq#<tr><th colspan=$colspan><hr size=4 noshade color="black"></th></tr>\n#;
  print "<tr>";
  print qq#<th> <input type="checkbox" name="select-all" id="select-all">Sel All</th>\n#;
  foreach $array (@arrays) {
    ($arrayname =  $array) =~ s/s$//;
    $arrayname =~ s/Number/#/gi;
    $arrayname =~ s/Check/Chk/gi;
    $arrayname =~ s/Amount/Amt/gi;
    $arrayname =~ s/PharmName/Name/gi;
    $arrayname =~ s/PaymentType/PYMT<br>Type/gi;
    $arrayname =~ s/DateAdded/Added/gi;
    print "<th align=left>$arrayname</th>";
    $linesprinted++;
  }
  print "</tr>\n";
}

#______________________________________________________________________________

sub doACTION {
  my ($ACTION, $TCode, $Notes) = @_;

  $NumOfRows  = 0;	# Default to zero for COMMIT/ROLLBACK code
  $NumOfRowsU = 0;
  $NumOfRowsA = 0;
  $NumOfRowsD = 0;
  $NumOfRowsTotal = 0;
  $outinfo = "";

  $sqlST = qq#START TRANSACTION#;
  ($p1) = &ReconRx_jdo_sql($sqlST);

  if ( $ACTION =~ /ADDNOTE/i ) {
     if ( $Notes =~ /^\s*$/i ) {
        print "No Notes Entered. Skipping<br>\n" if ($debug);
     } else {
       print "ADDING Notes!<br>Notes: $Notes<hr>\n";

       foreach $key (sort keys %in) {
          if ( $key =~ /^PCNR/i ) {
             $val = $in{$key};
             ($NCPDP,$PharmName,$TPP,$CheckNumber,$CheckAmount,$CheckDate,$DateAdded,$INNotes,$FLAG) = split("##", $val); 
             $CheckAmount =~ s/\$|,//g;
             print "Updating key: $key, val: $val<br>\n" if ($debug);
             print qq#($NCPDP,$PharmName,$TPP,$CheckNumber,$CheckAmount,$CheckDate,$DateAdded,$INNotes,$FLAG)<br>\n# if ($debug);

             $sql  = qq# UPDATE $DBNAME.$TABLE SET Notes='$Notes' #;
             $sql .= qq# WHERE (1=1) #;
             $sql .= qq# && NCPDP = $NCPDP #;
             $sql .= qq# && ThirdParty = '$TPP' #;
             $sql .= qq# && CheckNumber = '$CheckNumber' #;
             $sql .= qq# && CheckAmount = $CheckAmount #;
             $sql .= qq# && CheckDate = $CheckDate #;
             $sql .= qq# && DateAdded = $DateAdded #;
             
             ($sqlout = $sql) =~ s/\n/<br>\n/g;
             print "<br>doACTION Update sql:<br>\n$sqlout<br>\n" if ($debug);
             
             $sthx = $dbx->prepare($sql);
             $sthx->execute();
             
             $NumOfRows = $sthx->rows;
             print "Number of rows updated: $NumOfRows<br>\n" if ($debug);
             $NumOfRowsTotal += $NumOfRows;
              
             print "<hr>\n" if ($debug);
             $sthx->finish();
          }
       }
     }
 
  } elsif ( $ACTION =~ /ARCHIVE/i ) {
    foreach $key (sort keys %in) {
       if ( $key =~ /^PCNR/i ) {
          $val = $in{$key};
          ($NCPDP,$PharmName,$TPP,$CheckNumber,$CheckAmount,$CheckDate,$DateAdded,$INNotes,$FLAG) = split("##", $val); 
          $CheckAmount =~ s/\$|,//g;
          print "Updating key: $key, val: $val<br>\n" if ($debug);
          print qq#($NCPDP,$PharmName,$TPP,$CheckNumber,$CheckAmount,$CheckDate,$DateAdded,$INNotes,$FLAG)\n# if ($debug);
          $outinfo .= "$NCPDP,$PharmName,$TPP,$CheckNumber,$CheckAmount,$CheckDate,$DateAdded,$INNotes,$FLAG\n";

          $NewTCode = "$TCodeDate: $TCode";
          $sql  = qq# UPDATE $DBNAME.$TABLE SET TCode='$NewTCode' #;
          $sql .= qq# WHERE (1=1) #;
          $sql .= qq# && NCPDP = $NCPDP #;
          $sql .= qq# && ThirdParty = '$TPP' #;
          $sql .= qq# && CheckNumber = '$CheckNumber' #;
          $sql .= qq# && CheckAmount = $CheckAmount #;
          $sql .= qq# && CheckDate = $CheckDate #;
          $sql .= qq# && DateAdded = $DateAdded #;
          
          ($sqlout = $sql) =~ s/\n/<br>\n/g;
          print "<br>doACTION Update sql:<br>\n$sqlout<br>\n" if ($debug);
          
          $sthx = $dbx->prepare($sql);
          $sthx->execute();
          
          $NumOfRowsU = $sthx->rows;
          $sthx->finish();
          $NumOfRowsTotal += $NumOfRowsU;

          if ( $NumOfRowsU > 0 ) {
             $sql  = qq# REPLACE INTO $PADBNAME.$PATABLE #;
             $sql .= qq# SELECT * FROM $DBNAME.$TABLE #;
             $sql .= qq# WHERE (1=1) #;
             $sql .= qq# && NCPDP = $NCPDP #;
             $sql .= qq# && ThirdParty = '$TPP' #;
             $sql .= qq# && CheckNumber = '$CheckNumber' #;
             $sql .= qq# && CheckAmount = $CheckAmount #;
             $sql .= qq# && CheckDate = $CheckDate #;
             $sql .= qq# && DateAdded = $DateAdded #;
             
             ($sqlout = $sql) =~ s/\n/<br>\n/g;
             
             $sthx = $dbx->prepare($sql);
             $sthx->execute();
             
             $NumOfRowsA = $sthx->rows;

             if ( $NumOfRowsA > 0 ) {
        
                $sql  = qq# DELETE FROM $DBNAME.$TABLE #;
                $sql .= qq# WHERE (1=1) #;
                $sql .= qq# && NCPDP = $NCPDP #;
                $sql .= qq# && ThirdParty = '$TPP' #;
                $sql .= qq# && CheckNumber = '$CheckNumber' #;
                $sql .= qq# && CheckAmount = $CheckAmount #;
                $sql .= qq# && CheckDate = $CheckDate #;
                $sql .= qq# && DateAdded = $DateAdded #;
             
                ($sqlout = $sql) =~ s/\n/<br>\n/g;
             
                $sthx = $dbx->prepare($sql);
                $sthx->execute();
             
                $NumOfRowsD = $sthx->rows;
                $sthx->finish();
             }
          }
       }
    }
  } elsif ( $ACTION =~ /EXPORT/i ) {
    print "DO EXPORT!<br>\n" if ($debug);
    ($NumOfRowsTotal)  = &generateReport;
  }

  $commit = 0;
  if ( $ACTION =~ /ADDNOTE/i && $NumOfRows > 0 ) {
     $commit++;
  } elsif ( $ACTION =~ /ARCHIVE/i && $NumOfRowsU > 0 && $NumOfRowsA > 0 && $NumOfRowsD > 0 ) {
     $commit++;
  } elsif ( $ACTION =~ /EXPORT/i && $NumOfRows > 0 ) {
     $commit++;
  }

#  $commit = 0; # TESTING ONLY

  print qq#<table border="5" cellpadding=5 cellspacing=5 bordercolor="00FF00">\n#;
  print qq#<tr><td>\n#;
  if ( $commit ) {
     $sql  = qq#COMMIT; #;
     ($p1) = &ReconRx_jdo_sql($sql);
     print "<font size=+1 color=green>$ACTION completed successfully.</font><br>\n";
     if ( $ACTION =~ /ADDNOTE/i ) {
       print "Notes: '$Notes' added/updated on $NumOfRowsTotal record";
       print "s" if ( $NumOfRowsTotal > 1 );
     } elsif ( $ACTION =~ /ARCHIVE/i ) {
       $out = "Archived $NumOfRowsTotal record";
       $out .= "s" if ( $NumOfRowsTotal > 1 );
       $out .= " with TCODE: $TCode";
       $outinfo =~ s/\n/<br>\n/g;
       $out .= "<br>$outinfo";
       print "$out<br>\n";

       if ($OWNER !~ /^\s*$/) { $POSTER = $OWNER; } else { $POSTER = $USER; }
       &logActivity($POSTER, "$out", $USER);

     } elsif ( $ACTION =~ /EXPORT/i ) {
       print "Exported $NumOfRowsTotal record";
       print "s" if ( $NumOfRowsTotal > 1 );
     }
     print "<br>\n";
  } else {
     print "ROLLBACK- rowsReplaced: $rowsReplaced\n";
     $sql  = qq#ROLLBACK #;
     ($rowsfoundROLLBACK) = &ReconRx_jdo_sql($sql);
     print "\nROLLBACK ($rowsfoundROLLBACK)!!!!!!!!!!!\n\n" if ($debug);
     print "<HR><font size=+1 color=red>$ACTION unsuccessful! Rolling back changes!</font><br>\n";
  }
  print qq#</td></tr>\n#;
  print qq#</table>\n#;
  print qq#<HR color=red>\n#;

  $Notes = "";
}

#______________________________________________________________________________

sub inithashes {
  %NCPDPs       = ();
  %PharmNames   = ();
  %TPPs         = ();
  %CheckNumbers = ();
  %CheckAmounts = ();
  %CheckDates   = ();
  %DateAddeds   = ();
  %Notes        = ();
  %PaymentTypes = ();
  %FLAGs        = ();
}

#______________________________________________________________________________

sub generateReport {
  &setExcel($newExcel);
  $row = 0;
  $col = 0;

  open(CSVEXPORT, "> $newcsv") || die "Couldn't open output file '$newcsv'.<br>\n\t$!<br>\n<br>\n";

  my $sth0 = $dbx->prepare("SELECT * FROM $DBNAME.$TABLE WHERE 1=0;");
  $sth0->execute;
  my @colsn = @{$sth0->{NAME}}; # or NAME_lc if needed
  my @colst = @{$sth0->{mysql_type_name}};

  $ptr = 0;
  $HEADINGS = "";
  $TYPES    = "";

  foreach my $key ( @colsn ) {
    next if ( $key =~ /TCode|CheckReceivedDate/i );
    $$HASH{$key} = $colst[$ptr];
    printf ( "%s,%s<br>\n", $key, $colst[$ptr] ) if ($debug);

    $HEADINGS .= "$key,";
    $TYPES    .= "$colst[$ptr],";
    $DISPHEAD = $key;
    $DISPHEAD =~ s/R_//g;
    $DISPHEAD =~ s/By/ By /gi;
    $DISPHEAD =~ s/Check/Check /gi;
    $DISPHEAD =~ s/PaymentType/Payment Type/gi;
    $DISPHEAD =~ s/ThirdParty/Third Party/gi;
    $DISPHEAD =~ s/DateAdded/Date Added/gi;
    $DISPHEAD =~ s/ReceivedDate/Received Date/gi;

    &outExcel($headformat , $DISPHEAD); $col++;

    $REPFIELDS{$key} = $colst[$ptr];
    $REPFIELDSORDER{$key} = $ptr;
    $ptr++;
  }

  $sth0->finish;

  $HEADINGS =~ s/,$//g;
  $TYPES    =~ s/,$//g;
  print CSVEXPORT "$HEADINGS\n";
  print CSVEXPORT "$TYPES\n" if ($debug);

#	  foreach $key (sort keys { $REPFIELDSORDER{$a} <=> $REPFIELDSORDER{$b} } ) {
#	     print "$REPFIELDSORDER{$key} key: $key, $REPFIELDS{$key}<br>\n" if ($debug);
#	 
#	  }

  foreach $key (sort keys %in) {
     if ( $key =~ /^PCNR/i ) {
        $val = $in{$key};
        ($NCPDP,$PharmName,$TPP,$CheckNumber,$CheckAmount,$CheckDate,$DateAdded,$INNotes,$FLAG) = split("##", $val); 
        $CheckAmount =~ s/\$|,//g;

        $sql  = qq# SELECT $HEADINGS FROM $DBNAME.$TABLE #;
        $sql .= qq# WHERE (1=1) #;
        $sql .= qq# && NCPDP = $NCPDP #;
        $sql .= qq# && ThirdParty = '$TPP' #;
        $sql .= qq# && CheckNumber = '$CheckNumber' #;
        $sql .= qq# && CheckAmount = $CheckAmount #;
        $sql .= qq# && CheckDate = $CheckDate #;
        $sql .= qq# && DateAdded = $DateAdded #;
        
        ($sqlout = $sql) =~ s/\n/<br>\n/g;
        print "<br>doACTION SELECT sql:<br>\n$sqlout<br>\n" if ($debug);
        
        $sthx = $dbx->prepare($sql);
        $sthx->execute();
        
        $NumOfRows = $sthx->rows;
        print "Number of rows selected: $NumOfRows<br>\n" if ($debug);
        $NumOfRowsTotal += $NumOfRows;
      
        if ( $NumOfRows > 0 ) {
           while ( my @row = $sthx->fetchrow_array() ) {
	           print CSVEXPORT qq#"#, join(qq#","#, @row), qq#"\n#;
               $row++;
               $col = 0;
               foreach $pc (@row) {
                  &outExcel($format, $pc); $col++;
               }
           }
        } else {
          print "No Rows found!\n";
        }
        $sthx->finish();
     }
  }

  close (CSVEXPORT); 

  $worksheet->set_column( 0, 0,  8);	# NCPDP
  $worksheet->set_column( 1, 1, 10);	# Date Added
  $worksheet->set_column( 2, 2,  8);	# BIN
  $worksheet->set_column( 3, 3, 20);	# Third Party
  $worksheet->set_column( 4, 4,  9);	# Payment Type
  $worksheet->set_column( 5, 5, 16);	# Check Number
  $worksheet->set_column( 6, 6, 11);	# Check Amount
  $worksheet->set_column( 7, 7, 10);	# Check Date
  $worksheet->set_column( 8, 8, 30);	# Notes
  $worksheet->set_column( 9, 9, 11);	# Posted By
  $worksheet->set_column(10,10, 30);	# Posted By User
  $worksheet->set_column(11,11, 20);	# Posted By Date

  $workbook->close();
  
  return($NumOfRowsTotal);

}

#______________________________________________________________________________

sub setExcel {
  my ($SSName) = @_;

  $headformat = "";
  $format     = "";
  $dolformat  = "";

  unlink "$SSName" if ( -e "$SSName" );

  if ( $debug ) {
     if ( !-e "$SSName" ) {
       print "File Gone! $SSName<br>\n";
     } else {
       print "File still there! $SSName<br>\n";
     }
  }

  $workbook  = Excel::Writer::XLSX->new("$SSName");
  $worksheet = $workbook->add_worksheet();

  foreach $worksheet ($workbook->sheets()) {
     $worksheet->set_landscape();
     $worksheet->fit_to_pages(1,0);	# Fit all columns on a single page
     $worksheet->hide_gridlines(0);	# 0  -SHOW gridlines
     $worksheet->freeze_panes(1,0);	# 0  -Freeze first row
     $worksheet->repeat_rows(0);	# 0 - Print on each page
  }
  my $TITLE = $newExcelname;
  $worksheet->set_header("&C\&11\&\"Calibri,Regular\"$TITLE", 0.20);

  $worksheet->set_footer("\&L&D\&RPage &P of &N");
  $worksheet->repeat_rows(0);
  $worksheet->set_margin_left(0.30);
  $worksheet->set_margin_right(0.30);
 
  $workbook->set_properties(
      title    => "$report",
      author   => "ReconRx",
      comments => "$tdate $ttime",
      subject  => "$report"
  );

# binmode(STDOUT);

  $worksheet->add_write_handler(qr[\w], \&store_string_widths);

  $headformat = $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'left');
  $headformat->set_text_wrap();

  $headformatL= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'left');
  $headformatL->set_text_wrap();
  $headformatR= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'right');
  $headformatR->set_text_wrap();
  $headformatC= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'center');
  $headformatC->set_text_wrap();
  $headformatD= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'right', num_format => '$#,##0.00');
  $headformatD->set_text_wrap();
  $headformatI= $workbook->add_format(bold => 1, bg_color => 'cyan', font =>'Arial', align => 'left');
  $headformatI->set_italic();
  $headformatI->set_text_wrap();

  $format     = $workbook->add_format();
  $format->set_align('left');
  $format->set_font('Arial');
  $format->set_text_wrap();

  $formatL     = $workbook->add_format();
  $formatL->set_align('left');
  $formatL->set_font('Arial');
  $formatR    = $workbook->add_format();
  $formatR->set_align('right');
  $formatR->set_font('Arial');
  $formatR14    = $workbook->add_format();
  $formatR14->set_align('right');
  $formatR14->set_font('Arial');
  $formatR14->set_num_format('00000000000000');

  $formatC    = $workbook->add_format();
  $formatC->set_align('center');
  $formatC->set_font('Arial');
  $formatD    = $workbook->add_format();
  $formatD->set_align('right');
  $formatD->set_font('Arial');
  $formatD->set_num_format('$#,##0.00');	# Money!
  $formatGreen = $workbook->add_format();
  $formatGreen->set_align('left');
  $formatGreen->set_bg_color('lime');
  $formatBlue = $workbook->add_format();
  $formatBlue->set_align('right');
  $formatBlue->set_bg_color('cyan');
  $formatBlueD = $workbook->add_format();
  $formatBlueD->set_align('right');
  $formatBlueD->set_bg_color('cyan');
  $formatBlueD->set_bold;
  $formatBlueD->set_num_format('$#,##0.00');	# Money!

  $formatGreenD = $workbook->add_format();
  $formatGreenD->set_align('right');
  $formatGreenD->set_bg_color('lime');
  $formatGreenD->set_num_format('$#,##0.00');	# Money!

  print "sub setExcel. Exit.<br>\n" if ($debug);

}

#______________________________________________________________________________

sub outExcel {
   my ($format, $out) = @_;

   ($out) = &StripIt_local($out);
   if ( $out =~ /^\s*0\s*$/ ) {
      $out = "0.00";
   } elsif ( !$out ) {
      $out = " ";
   }
#  print "EXCEL: row: $row, col: $col, format: $format, out: $out<br>\n" if ($debug);
   if ( $format ) {
     $worksheet->write($row, $col, "$out", $format);
   } else {
     $worksheet->write($row, $col, "$out");
   }
}

#______________________________________________________________________________

sub StripIt_local {
   my ($value) = @_;

   $value =~ s/^\s*(.*?)\s*$/$1/;
   $value =~ s/\/\s+\///g;

   return($value);
}

#______________________________________________________________________________

sub display_Excel_if_exists {
  my $now = time();
  $URL1 = qq#/Reports/$newExcelname?TS=$now#;
  $URL1 =~ s/ /\%20/g;
  $URL2 = qq#/Reports/$newcsvname?TS=$now#;
  $URL2 =~ s/ /\%20/g;

  print "URL1: $URL1<br><br>\n" if ($debug);
  print "URL2: $URL2<br><br>\n" if ($debug);

  print qq#<table>\n#;
  if ( -e "$newExcel" ) {
     print qq#<tr><th>Excel Export: </th><th> <a href="$URL1" target=new>$newExcelname</a></th></tr>#;
  }
  if ( -e "$newcsv" ) {
     print qq#<tr><th>CSV   Export: </th><th> <a href="$URL2" target=new>$newcsvname</a></th></tr>#;
  }
  print qq#</table>\n#;
}

#______________________________________________________________________________
