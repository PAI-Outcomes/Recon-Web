require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use Date::Format;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$TS         = $in{'TS'};
$TPP        = $in{'TPP'};
$Q          = $in{'Q'};

($TS)    = &StripJunk($TS);
($TPP)   = &StripJunk($TPP);

%ListAtBottom = ();
%plb_total    = ();
%payers       = ();

#______________________________________________________________________________

&readsetCookies;
&readPharmacies;

#______________________________________________________________________________
my $agg_check;
if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    $agg_check = 1;
    &ReconRxAggregatedHeaderBlock_New;
  }
  else {
    &ReconRxHeaderBlock;
  }
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

if ( $PH_ID  eq 'Aggregated') {
  $PH_ID = $Agg_String;
}

my $R8DBNAME = "";
my $P8DBNAME = "";

if ($PH_ID == 11 || $PH_ID == 23 || $PHY_ID eq "11,23") {
	$R8DBNAME = "webinar";
    $P8DBNAME = "webinar";
} else {
	$R8DBNAME = "reconrxdb";
    $P8DBNAME = "reconrxdb";
}


#______________________________________________________________________________

%attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error );
$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST", $dbuser,$dbpwd, \%attr) || &handle_error;
DBI->trace(1) if ($dbitrace);

&readThirdPartyPayers;
&read_Other_Sources_835s;
&read_Other_Sources_835s_Lookup;

#______________________________________________________________________________
#

($ENV) = &What_Env_am_I_in;
&displayWebPage;

#______________________________________________________________________________

&MyReconRxTrailer;

# Close the Database
$dbx->disconnect;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
   print qq#<!-- displayWebPage -->\n#;
   my $check_tbl = 'checks';

   $FMT = "%0.02f";
   my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
   my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($TS);
   $year += 1900;
   $date    = qq#$abbr[$mon] $mday, $year#; 
   $DATE    = sprintf("%02d/%02d/%04d", $mon+1, $mday, $year);
   $SFDATE  = sprintf("%04d-%02d-%02d", $year, $mon+1, $mday);
   $SFDATE2 = sprintf("%04d-%02d-%02d",   $year, $mon+1, $mday);

   $SFDATE2 =~ s/\-//g if ( $Q =~ /CD/i );

   ($PROG = $prog) =~ s/_/ /g;

   print qq#<a href="javascript:history.go(-1)">Return</a><br>\n#;
   &check_missing_PLBS(); # if ($Pharmacy_CentralPayOrgs{$PH_ID} =~ /Health Mart Atlas|AlignRx/);

   print qq#<table>\n#;
   print qq#<tr><th colspan=3><h2 class="page_title">Third Party Payer Check List: #;

   if ( $TPP ) {
      print qq#$TPP#;
   } else {
      print qq#$date#;
   }

   print qq#</h2></th>\n#;
   print qq#<th colspan=4>\n#;
   ($TSx) = &set_TSx($TS, $SFDATE2);
   
     print "<th style='font-size:100%'>";

   print qq#
      Export to Excel:<br>
    <div style="border: 2px solid black; text-align:center">#;
    
     $URLH = "Retrieve_Checks_All.cgi";
     print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return validate(this)\;">\n#;
     print qq#<INPUT TYPE="hidden" NAME="Q"       VALUE="$Q">\n#;
     print qq#<INPUT TYPE="hidden" NAME="TYPE"    VALUE="$TYPE">\n#;
     print qq#<INPUT TYPE="hidden" NAME="CHK"     VALUE="ALL">\n#;
     print qq#<INPUT TYPE="hidden" NAME="CD"      VALUE="$CD">\n#;
     print qq#<INPUT TYPE="hidden" NAME="TS"      VALUE="$TS">\n#;

   print qq#
        <INPUT  style="top: 0px; padding:0px; margin:0px; width: 96%" TYPE="Submit"
          NAME="submit_checks" VALUE="Checks"><br>
     #;

   print qq#</FORM>\n#;
   
   $URLH = "Retrieve_Remit_All.cgi";
   print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return validate(this)\;">\n#;
   print qq#<INPUT TYPE="hidden" NAME="Q"       VALUE="$Q">\n#;
   print qq#<INPUT TYPE="hidden" NAME="TYPE"    VALUE="$TYPE">\n#;
   print qq#<INPUT TYPE="hidden" NAME="CHK"     VALUE="ALL">\n#;
   print qq#<INPUT TYPE="hidden" NAME="CD"      VALUE="$CD">\n#;
   print qq#<INPUT TYPE="hidden" NAME="TS"      VALUE="$TS">\n#;
   print qq#<INPUT TYPE="hidden" NAME="ISA06"       VALUE="$R_ISA06_Interchange_Sender_ID">\n#;
   print qq#<INPUT TYPE="hidden" NAME="SFDATE2"     VALUE="$SFDATE2">\n#;
   print qq#<INPUT TYPE="hidden" NAME="TPPPRI"      VALUE="$records_TPP_PRI{$key}">\n#;
   print qq#<INPUT TYPE="hidden" NAME="SFDATE2"     VALUE="$SFDATE2">\n#;
   print qq#<INPUT TYPE="hidden" NAME="REF02"       VALUE="$R_REF02_Value">\n#;
   print qq#<INPUT TYPE="hidden" NAME="OtherSource" VALUE="$OtherSource">\n#;
   print qq#<INPUT TYPE="hidden" NAME="DISPTPPID"   VALUE="$Display_TPPID">\n#;
   print qq#<INPUT TYPE="hidden" NAME="DISPonRemit" VALUE="$Display_on_Remits">\n#;
   
   print qq#<INPUT  style="top: 0px; padding:0px; margin:0px; width: 96%" TYPE="Submit"
   NAME="Submit" VALUE="Claims">\n#;

   print qq#</FORM>\n#;
   print qq#</div>#;
   print qq#</div>\n#;

   print qq#</th>\n#;
   print qq#</tr>\n#;
   my $ncpdp = "<th>NCPDP</th>" if $agg_check;
   print qq#<tr><th>Payer</th>$ncpdp<th>Payment Type</th> <th>Check or<br>ACH \#</th> <th>Check Amt</th> <th>Check Date</th> <th>Count</th> <th>Print Remit</th> </tr>\n#;

#  # selected a Date from previous page

   $sql  = "SELECT Check_ID, R_TPP, R_TS3_NCPDP, R_BPR04_Payment_Method_Code, R_BPR02_Check_Amount, 
                   R_BPR16_Date, R_TRN02_Check_Number, R_PENDRECV, R_PostedBy,
                   R_TPP_PRI, Payer_ID, Third_Party_Payer_Name, 
                   CASE WHEN R_TPP_PRI != Payer_ID THEN R_REF02_Value ELSE '' END AS ref02,
                   ROUND(SUM(R_CLP04_Amount_Payed),2) as sum, count(*) as cnt
              FROM ( SELECT a.Check_ID, a.R_TPP, a.R_TS3_NCPDP, a.R_BPR04_Payment_Method_Code, a.R_BPR02_Check_Amount, 
                            a.R_BPR16_Date, a.R_TRN02_Check_Number, a.R_PENDRECV, a.R_ISA06_Interchange_Sender_ID, a.R_PostedBy, 
                            a.R_TPP_PRI, b.R_REF02_Value, b.Payer_ID, b.R_CLP04_Amount_Payed
                       FROM $P8DBNAME.$check_tbl a
                       JOIN $P8DBNAME.$P8TABLE b ON ( a.Check_ID = b.Check_ID )
                      WHERE a.Pharmacy_ID IN ($PH_ID)
                        AND a.R_PENDRECV = 'R'
                        AND ";

   if ( $Q =~ /CRD/i ) {
      $sql .= " a.R_CheckReceived_Date='$SFDATE2' ";
   } else {
      $sql .= " a.R_BPR16_Date='$SFDATE2' ";
   }
   $sql .= "      UNION ALL
                     SELECT a.Check_ID, a.R_TPP, a.R_TS3_NCPDP, a.R_BPR04_Payment_Method_Code, a.R_BPR02_Check_Amount, 
                            a.R_BPR16_Date, a.R_TRN02_Check_Number, a.R_PENDRECV, a.R_ISA06_Interchange_Sender_ID, a.R_PostedBy, 
                            a.R_TPP_PRI, b.R_REF02_Value, b.Payer_ID, b.R_CLP04_Amount_Payed
                       FROM $R8DBNAME.$check_tbl a
                       JOIN $R8DBNAME.$R8TABLE b ON ( a.Check_ID = b.Check_ID )
                      WHERE a.Pharmacy_ID IN ($PH_ID)
                        AND a.R_PENDRECV='R'
                        AND ";

   if ( $Q =~ /CRD/i ) {
      $sql .= " a.R_CheckReceived_Date='$SFDATE2' ";
   } else {
      $sql .= " a.R_BPR16_Date='$SFDATE2' ";
   }

   $sql .= " ) a 
             JOIN officedb.third_party_payers b ON ( a.Payer_ID = b.Third_Party_Payer_ID )
         GROUP BY a.Check_ID, a.Payer_ID
         ORDER BY b.Third_Party_Payer_Name, a.R_BPR04_Payment_Method_Code, a.R_TRN02_Check_Number, a.R_BPR02_Check_Amount, a.R_BPR16_Date";

 
   $stb = $dbx->prepare($sql);
   $numofrows = $stb->execute;

   my $daily_total =0;

   if ( $numofrows > 0 ) {
     while (my @row = $stb->fetchrow_array()) {
       ($Check_ID, $R_TPP, $R_TS3_NCPDP, $R_BPR04_Payment_Method_Code, $R_BPR02_Check_Amount,
        $R_BPR16_Date, $R_TRN02_Check_Number, $R_PENDRECV, $R_PostedBy,
        $R_TPP_PRI, $Payer_ID, $payer_name, $R_REF02_Value, $claim_total, $claim_count) = @row;

       if ( $R_REF02_Value !~ /^\s*$/ ) {
          $ListAtBottom{$Check_ID} = $R_TRN02_Check_Number;
       }

       my $plb_key = "$Check_ID##$Payer_ID";
       
       print '<tr>';
       print "<td>$payer_name</td>";
       print "<td>$R_TS3_NCPDP</td>" if ($agg_check);
       print "<td>$R_BPR04_Payment_Method_Code</td>";
       print "<td class='align_right'>$R_TRN02_Check_Number</td>";

#       if ( $R_TPP_PRI != $Payer_ID ) {
       if ( $R_TPP_PRI =~ /700470|700929/ ) {
         $chk_amt = $claim_total - $plb_total{$plb_key};
       }
       elsif ( $R_TPP_PRI =~ /700447/ ) {
         print "2:$Check_ID...$Payer_ID " if ($USER == 66);
         if($plb_total{$plb_key}) {
           $chk_amt = $claim_total - $plb_total{$plb_key} ;
             print "$plb_key\n" if ($USER == 66);
         }
         else {
           $chk_amt = $claim_total;
         }
       }
       else {
         $chk_amt = $R_BPR02_Check_Amount;
       }

       $daily_total += $chk_amt;

       my $chk_amt_out = "\$" . &commify(sprintf("$FMT", $chk_amt));
       print qq#<td class="align_right">$chk_amt_out</a></td>#;

       my $Odate = substr($R_BPR16_Date, 4, 2) . "/" .  substr($R_BPR16_Date, 6, 2) . "/" .  substr($R_BPR16_Date, 0, 4);
       print qq#<td class="align_right">$Odate</a></td>#;

       print qq#<td class="align_right">$claim_count</td>\n#;

       print "<td>\n";
       $URLH = "Retrieve_Remit.cgi";
       print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return validate(this)\;">\n#;
       print qq#<INPUT TYPE="hidden" NAME="SRC"         VALUE="chklist">\n#;
       print qq#<INPUT TYPE="hidden" NAME="Check_ID"    VALUE="$Check_ID">\n#;
       print qq#<INPUT TYPE="hidden" NAME="Payer_ID"    VALUE="$Payer_ID">\n#;
       print qq#<INPUT TYPE="hidden" NAME="TPPPRI"      VALUE="$R_TPP_PRI">\n#;
       print qq#<INPUT TYPE="hidden" NAME="CHKNUM"      VALUE="$R_TRN02_Check_Number">\n#;
       print qq#<INPUT TYPE="hidden" NAME="CHKDATE"     VALUE="$Odate">\n#;
       print qq#<INPUT TYPE="hidden" NAME="REF02_STR"   VALUE="$str_ref02">\n#;
       print qq#<INPUT TYPE="hidden" NAME="PostedBy"    VALUE="$R_PostedBy">\n#;
       print qq#<INPUT TYPE="hidden" NAME="DISPCHKAMT"  VALUE="$chk_amt_out">\n#;
       print qq#<INPUT style="float: right; position: relative; top: 0px; padding:0px; margin:0px" TYPE="Submit" NAME="Submit" VALUE="Retrieve Remit">\n#;

       print qq#</FORM>\n#;
       print "<br>\n";

       print "</td>\n";

       if ($R_PostedBy =~ /recon/i) {
          $R_PostedByTD = '<img src="/images/reconrx16px.png">';
       } else {
          $R_PostedByTD = '<div style="min-width: 16px;"></div>';
       }

       print qq#<td class="no_border">$R_PostedByTD</td>#;
       print qq#</tr>\n#;
     }

     foreach $plbs (sort keys %missingplb) {
       $type = 'Adjustments';
       ($pcheck,$pcheckdate,$pplb)  =  split("##", $plbs);
       ##next if ( $pplb =~ /Arete/i && $payers{'700470'});###TOOK THIS OUT 20221205 BECAUSE REMITS WEREN'T BALANCING.   HAD ARETE ADJUSTMENT.   EX(NCPDP 0328270 CHECK 4230375, 4245815)
       $amount = $missingplb{$plbs};
       print qq#<tr>\n#;
             print qq#<td>#;
             print qq#$type#;
             print qq#</td>#;
             print qq#<td>#;
             print qq##;
             print qq#</td>#;
             print qq#<td class="align_right">#;
             print qq#$pcheck#;
             print qq#</td>#;
             print qq#<td class="align_right">#;
             $daily_total -= $amount;
             $amount = "\$" . &commify(sprintf("$FMT", $amount));
             print qq#$amount#;
             print qq#</td>#;
             print qq#<td class="align_right">#;
             my $Odate = substr($pcheckdate, 4, 2) . "/" .  substr($pcheckdate, 6, 2) . "/" .  substr($pcheckdate, 0, 4);
             print qq#$Odate#;
             print qq#</td>#;
       print qq#</tr>\n#;
     }

     my $dtout = "\$" . &commify(sprintf("$FMT", $daily_total));
     print qq#<tr><th colspan=3 class="align_right">#;
     if ( $TPP ) {
        print qq#$TPP #;
     } else {
        print qq#$date #;
     }
     print qq#Total:</th> <th class="align_right">$dtout</td> <th colspan=3>$nbsp</th></tr>#;

     $firstone++;
     $countOfFileNotFound = 0;
     foreach $Check_ID (sort keys %ListAtBottom) {
        if ($firstone) {
           print qq#<tr><th colspan=1>$nbsp</th> <th colspan=6 class="align_left"><br>Download Central Pay 835 for check:</th></tr>\n#;
          $firstone = 0;
        }

        print "Check_ID: $Check_ID, Check#: $ListAtBottom{$Check_ID} Q: $Q, SFDATE2: $SFDATE2<br>\n" if ($debug);

#        ($DateAdded, $my835Filename) = &set835($CheckNumber, $Q, $SFDATE2);
        ($DateAdded, $my835Filename) = &set835($Check_ID);
        print "<hr>DateAdded: $DateAdded<br>my835Filename: $my835Filename<hr>\n" if ($debug);

        my $my835fn = $my835Filename;
        print "<br>\nmy835Filename: $my835Filename<br><br>\n" if ($debug);
        print "my835fn: $my835fn<br>\n" if ($debug);

        $old_server = 'pasrvc';
        $new_server = $FLSERVER;
        my $jfname = $my835fn;
#        print qq#jfname =~ s/$old_server/$new_server/gi<br>\n#;
        $jfname =~ s/$old_server/$new_server/gi;

        print "jfname: $jfname<br>\n" if ($debug);
        if ( -d "$jfname" ) {
           my @pcs = split(/\\/, $my835fn);
           $jfname .= "\\" . $pcs[$#pcs];
        }
        if ( !-e "$jfname" && $countOfFileNotFound == 0 ) {
           if ( $ENV =~ /Dev/i ) {
              print qq#<font bgcolor=yellow>835 file not found.<br>$jfname<br>#;
              print qq#Please <a href="/cgi-bin/Contact_Us.cgi">contact</a> ReconRx for assistance.</font><br>\n#;
           }
	   $countOfFileNotFound++;
        }
   
        my $outline = "";
        ##$jfname =~ s/\\/\\\\/g;
        if ( -e "$jfname" ) {
           open(FILE, "< $jfname") || die "Couldn't open input file '$jfname'<br>\n$!<br><br>\n";
           while (<FILE>) {
              $outline .= $_;
           }
           close(FILE);
        } else {
           $outline = "No file found: $jfname<br>\n";
        }
   
        $outdir = qq#D:/Recon-Rx/Reports#;
        $REPORT = "my835";
        $fname = "${REPORT}_${SFDATE2}_${ListAtBottom{$Check_ID}}.txt";
        my $outfilename = qq#$outdir/$fname#;
        if ( !-e "$outfilename" && "$outfilename" !~ /.txt/i ) {
             $outfilename .= ".txt";
        }
   
        open(OFILE, "> $outfilename") || die "Couldn't open output file '$outfilename'<br>\n$!<br><br>\n";
        print OFILE "$outline\n";
        close(OFILE);
    
        my $now = time();
        $URL = qq#/reports/$fname?TS=$now#;  
        $URL =~ s/ /\%20/g;
        print "URL: $URL<br><br>\n" if ($debug);
   
        print qq#<tr><th colspan=2>$nbsp</th> <th colspan=5 class="align_left"><a href="$URL" target=new>$ListAtBottom{$Check_ID}</a></th></tr>\n#;

     }
     print qq#</table>\n#;
   }
   $stb->finish;

}

#______________________________________________________________________________

sub check_missing_PLBS {
my $R8DBNAME = "";
my $P8DBNAME = "";
#print "PH_ID: $PH_ID\n";
if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23") {
	$R8DBNAME = "webinar";
    $P8DBNAME = "webinar";
} else {
	$R8DBNAME = "reconrxdb";
    $P8DBNAME = "reconrxdb";
}
  my $R8dbin     = "R8DBNAME";
  #my $R8DBNAME = $DBNAMES{"$R8dbin"};
  my $R8TABLE  = $DBTABN{"$R8dbin"};

  my $P8dbin     = "P8DBNAME";
  #my $P8DBNAME = $DBNAMES{"$P8dbin"};
  my $P8TABLE  = $DBTABN{"$P8dbin"};
  
  #print "R8DBNAME: $R8DBNAME\n";
  #print "P8DBNAME: $P8DBNAME\n";
 
  my $sql = "SELECT a.R_TRN02_Check_Number, b.R_REF02_Value, b.Payer_ID
               FROM $P8DBNAME.checks a
               JOIN $P8DBNAME.$P8TABLE b ON (a.Check_ID = b.Check_ID) 
              WHERE a.Pharmacy_ID IN ($PH_ID)
                AND a.R_PENDRECV = 'R'
                AND ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " a.R_CheckReceived_Date='$SFDATE2' ";
  } else {
     $sql .= " a.R_BPR16_Date='$SFDATE2' ";
  }

  $sql .= " UNION ALL
               SELECT a.R_TRN02_Check_Number, b.R_REF02_Value, b.Payer_ID
                 FROM $R8DBNAME.checks a
               JOIN $P8DBNAME.$R8TABLE b ON (a.Check_ID = b.Check_ID)
                WHERE a.Pharmacy_ID IN ($PH_ID)
                  AND a.R_PENDRECV = 'R'
                  AND ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " a.R_CheckReceived_Date='$SFDATE2' ";
  } else {
     $sql .= " a.R_BPR16_Date='$SFDATE2' ";
  }

  $sql .= " GROUP BY a.R_TRN02_Check_Number, b.R_REF02_Value, b.Payer_ID";
##print "$sql\n" if ($USER == 66);
  $stb = $dbx->prepare($sql);
  $numofrows = $stb->execute;

  while (my @row = $stb->fetchrow_array()) {
    $reflist{$row[0]}{$row[1]}++;
    $payers{$row[2]}++;
  }

  $sql = "SELECT a.Check_ID, a.R_BPR16_Date, a.R_TRN02_Check_Number, a.R_TPP_PRI, b.Adjustment_Description, b.Adjustment_Amount
            FROM $R8DBNAME.checks a
            JOIN $R8DBNAME.check_plbs b ON (a.Check_ID = b.Check_ID)
           WHERE a.Pharmacy_ID IN ($PH_ID)
             AND a.R_PENDRECV = 'R'
             AND ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " R_CheckReceived_Date='$SFDATE2' ";
  } else {
     $sql .= " R_BPR16_Date='$SFDATE2' ";
  }

  $sql .= "AND b.Reference_Identification <> ''";
## print "sql3: $sql\n" if($USER == 66);
  $stb = $dbx->prepare($sql);
  $numofrows = $stb->execute;

  while (my @row = $stb->fetchrow_array()) {
     ($check_id, $checkdate, $check, $tpp_pri, $plbdscr, $plbamt) = @row;

     ($p1,$plb) = split("\\[","$row[4]");
     $plb =~ s/\]//g;
     $plb = uc($plb);

     if ( $tpp_pri =~ /700470|700447/ ) {
       if ($tpp_pri =~ /700470/ && !$plb && $plbdscr =~ /\//) {
         $plbdscr =~ s/\///g;
         $plb = $plbdscr;
       }

       $key="$tpp_pri##$plb";

       if ( $Lookup_TPP_Display_on_Remit_TPP_IDs{$key} ) {
         my $lkey = "$check_id##$Lookup_TPP_Display_on_Remit_TPP_IDs{$key}";

         if ($plb_total{$lkey}) {
           $plb_total{$lkey} += $plbamt;
           next;
         }
       }
     }

     if ( $tpp_pri =~ /700929/ ) {
       $plb = $plbdscr; 
     }

     if($plb && !$reflist{$check}{$plb}){
         print "here:$plbamt\n" if ($USER == 66);
       $missingplb{"$check##$checkdate##$plb"} += $plbamt;
     }
  }
}

#______________________________________________________________________________

sub set_TSx {
  my ($TS, $date) = @_;

  $TSx  = "";
  if ( $TS > 0 ) {
     $TSx = "";
  } else {
     my $newdate = substr($date,0,4) . "-" . substr($date,4,2) . "-" . substr($date,6,2);
     ($TSx) = &build_date_TS($newdate);
  }

  return($TSx);
}

#______________________________________________________________________________

sub calc_OtherSource_Check_Amount {
  my ($inNCPDP, $SFDATE2, $REF02_Value, $CheckNumber) = @_;
  my $PLB_REF02 = $REF02_Value;
  $PLB_REF02 =~ s/'//g;
  $PLB_REF02 =~ s/,/\|/g;
  $PLB_REF02 =~ s/\|\|/\|/g;
  $PLB_REF02 =~ s/^\|//g;
  $PLB_REF02 =~ s/\|$//g;

  my $NEW_Check_Amount = 0;
  my $Amount_Payed = 0;
  my $Amount_PLBs  = 0;
  my $COUNT        = 0;
  
my $R8DBNAME = "";
my $P8DBNAME = "";

if ($PH_ID == 11 || $PH_ID == 23 || $PHY_ID eq "11,23") {
	$R8DBNAME = "webinar";
    $P8DBNAME = "webinar";
} else {
	$R8DBNAME = $DBNAMES{"$R8dbin"};
    $P8DBNAME = $DBNAMES{"$P8dbin"};
}

  my $R8dbin     = "R8DBNAME";
  #my $R8DBNAME = $DBNAMES{"$R8dbin"};
  my $R8TABLE  = $DBTABN{"$R8dbin"};

  my $P8dbin     = "P8DBNAME";
  #my $P8DBNAME = $DBNAMES{"$P8dbin"};
  my $P8TABLE  = $DBTABN{"$P8dbin"};
  
  print "R8DBNAME2: $R8DBNAME\n";
  print "P8DBNAME2: $P8DBNAME\n";
  
  print "R8DBNAME3: $R8DBNAME\n";
  print "P8DBNAME3: $P8DBNAME\n";

  my $sql = "";

#  # selected a Date from previous page
  $sql  = "SELECT round(sum(sum),2), sum(cnt)
             FROM (  SELECT sum(R_CLP04_Amount_Payed) as sum, count(*) as cnt 
                      FROM $P8DBNAME.$P8TABLE
                      WHERE Pharmacy_ID IN ($PH_ID)
                         && R_PENDRECV = 'R'
                         && R_REF02_Value IN ($REF02_Value)
                         && R_TRN02_Check_Number = '$CheckNumber' 
                         && ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " R_CheckReceived_Date='$SFDATE2' \n";
  } else {
     $sql .= " R_BPR16_Date='$SFDATE2' \n";
  }

  $sql .= "      UNION ALL
                     SELECT sum(R_CLP04_Amount_Payed) as sum, count(*) as cnt
                      FROM $R8DBNAME.$R8TABLE
                      WHERE Pharmacy_ID IN ($PH_ID)
                         && R_PENDRECV = 'R'
                         && R_REF02_Value IN ($REF02_Value)
                         && R_TRN02_Check_Number = '$CheckNumber' 
                         && ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " R_CheckReceived_Date='$SFDATE2' \n";
  } else {
     $sql .= " R_BPR16_Date='$SFDATE2' \n";
  }

  $sql .= " ) a \n";

  (my $sqlout = $sql) =~ s/\n/<br>\n/g;
  #print "sql: $sql\n";
  $stAmounts = $dbx->prepare($sql);
  $numofrows = $stAmounts->execute;
  print "numofrows: $numofrows<br>\n" if ($debug);

  if ( $numofrows > 0 ) {
    while (my @row = $stAmounts->fetchrow_array()) {
      ($Amount_Payed, $COUNT) = @row;
    }
  } else {
    $Amount_Payed = 0;
    $Amount_PLBs  = 0;
    $COUNT        = 0;
  }
  $stAmounts->finish;

  $sql  = "SELECT ROUND(SUM(Adjustment_Amount),2)
             FROM $P8DBNAME.checks a
             JOIN $P8DBNAME.check_plbs b ON ( a.check_id = b.check_id && b.Adjustment_Description REGEXP '($PLB_REF02)')
            WHERE a.Pharmacy_ID IN ($PH_ID)
              AND a.R_PENDRECV = 'R'
              AND a.R_TRN02_Check_Number = '$CheckNumber' 
              AND ";

  if ( $Q =~ /CRD/i ) {
     $sql .= " R_CheckReceived_Date='$SFDATE2'";
  } else {
     $sql .= " R_BPR16_Date='$SFDATE2'";
  }

  (my $sqlout = $sql) =~ s/\n/<br>\n/g;
  #print "sql2: $sql\n";
  $stAmounts = $dbx->prepare($sql);
  $numofrows = $stAmounts->execute;
  print "numofrows: $numofrows<br>\n" if ($debug);

  if ( $numofrows > 0 ) {
    while (my @row = $stAmounts->fetchrow_array()) {
      ($Amount_PLBs) = @row;
    }
  } else {
    $Amount_PLBs  = 0;
  }
  $stAmounts->finish;

  $NEW_Check_Amount = $Amount_Payed - $Amount_PLBs;

  return($NEW_Check_Amount, $COUNT);
}

#______________________________________________________________________________
