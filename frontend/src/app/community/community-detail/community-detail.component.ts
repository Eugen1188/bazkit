import {
  CommonModule
} from '@angular/common';

import {
  Component,
  OnInit
} from '@angular/core';

import {
  FormsModule
} from '@angular/forms';

import {
  ActivatedRoute,
  Router
} from '@angular/router';

import {
  CommunityComment,
  CommunityPost
} from '../../models/community.model';

import {
  CommunityService
} from '../../services/community.service';


@Component({
  selector:
    'app-community-detail',

  standalone:
    true,

  imports: [
    CommonModule,
    FormsModule
  ],

  templateUrl:
    './community-detail.component.html',

  styleUrl:
    './community-detail.component.scss'
})
export class CommunityDetailComponent
implements OnInit {

  post:
    CommunityPost | null =
      null;


  comments:
    CommunityComment[] =
      [];


  commentText =
    '';


  isLoading =
    true;

  isSubmittingComment =
    false;

  isCopying =
    false;


  message =
    '';

  errorMessage =
    '';


  stars = [
    1,
    2,
    3,
    4,
    5
  ];


  constructor(
    private route:
      ActivatedRoute,

    private router:
      Router,

    private communityService:
      CommunityService
  ) {}


  ngOnInit():
    void {

    const id =
      Number(
        this.route.snapshot
          .paramMap
          .get(
            'id'
          )
      );


    if (
      !id
    ) {

      this.router.navigate([
        '/main/community'
      ]);

      return;
    }


    this.loadPost(
      id
    );

    this.loadComments(
      id
    );
  }


  loadPost(
    id:
      number
  ): void {

    this.isLoading =
      true;


    this.communityService
      .getPost(
        id
      )
      .subscribe({

        next:
          post => {

            this.post =
              post;

            this.isLoading =
              false;
          },


        error:
          error => {

            console.error(
              'Community-Beitrag konnte nicht geladen werden:',
              error
            );

            this.isLoading =
              false;

            this.errorMessage =
              'Der Beitrag konnte nicht geladen werden.';
          }

      });
  }


  loadComments(
    id:
      number
  ): void {

    this.communityService
      .getComments(
        id
      )
      .subscribe({

        next:
          comments => {

            this.comments =
              comments;
          },


        error:
          error => {

            console.error(
              'Kommentare konnten nicht geladen werden:',
              error
            );
          }

      });
  }


  goBack():
    void {

    this.router.navigate([
      '/main/community'
    ]);
  }


  toggleLike():
    void {

    if (
      !this.post
    ) {

      return;
    }


    this.communityService
      .toggleLike(
        this.post.id
      )
      .subscribe({

        next:
          response => {

            if (
              !this.post
            ) {

              return;
            }


            this.post.liked_by_me =
              response.liked;

            this.post.like_count =
              response.like_count;
          }

      });
  }


  rate(
    value:
      number
  ): void {

    if (
      !this.post
      ||
      this.post.post_type ===
        'thread'
    ) {

      return;
    }


    this.communityService
      .ratePost(
        this.post.id,
        value
      )
      .subscribe({

        next:
          response => {

            if (
              !this.post
            ) {

              return;
            }


            this.post.my_rating =
              response.rating;

            this.post.rating_average =
              response.rating_average;

            this.post.rating_count =
              response.rating_count;
          }

      });
  }


  submitComment():
    void {

    if (
      !this.post
    ) {

      return;
    }


    const content =
      this.commentText
        .trim();


    if (
      !content
    ) {

      return;
    }


    this.isSubmittingComment =
      true;


    this.communityService
      .createComment(
        this.post.id,
        content
      )
      .subscribe({

        next:
          comment => {

            this.comments.push(
              comment
            );

            this.commentText =
              '';

            this.isSubmittingComment =
              false;


            if (
              this.post
            ) {

              this.post.comment_count =
                this.comments.length;
            }
          },


        error:
          error => {

            console.error(
              'Kommentar konnte nicht erstellt werden:',
              error
            );

            this.isSubmittingComment =
              false;
          }

      });
  }


  copyToMyAccount():
    void {

    if (
      !this.post
      ||
      this.post.post_type ===
        'thread'
    ) {

      return;
    }


    this.isCopying =
      true;

    this.message =
      '';


    this.communityService
      .copyPost(
        this.post.id
      )
      .subscribe({

        next:
          response => {

            this.isCopying =
              false;

            this.message =
              response.detail;
          },


        error:
          error => {

            console.error(
              'Übernahme fehlgeschlagen:',
              error
            );

            this.isCopying =
              false;

            this.message =
              'Der Inhalt konnte nicht übernommen werden.';
          }

      });
  }

}